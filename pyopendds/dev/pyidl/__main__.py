import argparse
import glob
import os
import os.path
import subprocess
import sys

from zipfile import ZipFile
from .gencmakefile import gen_cmakelist


def prompt(question):
    yes = {'yes', 'y'}
    no = {'no', 'n', ''}

    choice = input(question).lower()
    if choice in yes:
        return True
    elif choice in no:
        return False
    else:
        sys.stdout.write("Please respond with 'yes' or 'no'")


def get_base_prefix_compat():
    return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix


def in_virtualenv():
    return get_base_prefix_compat() != sys.prefix


def resolve_wildcard(expr, dir_name) -> list:
    files = glob.glob(f'{dir_name}/{expr}')
    rem_part = (len(dir_name) + 1)
    return list(map(lambda s: s[rem_part:], files))


def subprocess_check_run(commands: list, cwd: str, env=None, description: str = ""):
    try:
        subprocess.run(commands, cwd=cwd, check=True, env=env)
    except subprocess.CalledProcessError as err:
        print()  # print blank line
        if description:
            print(description)

        print(f"An error occured with the following command:\n"
              f"\tCWD: {cwd}\n"
              f"\tCMD: {' '.join(err.cmd)}\n"
              f"Exiting pyidl with status {err.returncode}.")
        sys.exit(err.returncode)


def extract_include_path_from_egg(output_dir: str):
    # potentially is into a egg archive
    script_path = os.path.dirname(os.path.realpath(__file__))
    root_path = os.path.realpath(f'{script_path}/../../..')
    include_dir = f'{output_dir}/include'
    sub_path = 'pyopendds/dev/include'

    if os.path.isfile(root_path) and root_path.lower().endswith('.egg'):
        with ZipFile(root_path, 'r') as zipObj:
            source_dir_path = f'{output_dir}/pyopendds/dev/include'
            for fileName in zipObj.namelist():
                if fileName.startswith(sub_path):
                    zipObj.extract(fileName, output_dir)
            subprocess.run(['mv', source_dir_path, include_dir])
            subprocess.run(['rm', '-r', f'{output_dir}/pyopendds'])
        return include_dir
    else:
        return f'{root_path}/{sub_path}'


def add_include_path(args: argparse.Namespace, filepath: str):
    dirname = os.path.dirname(os.path.realpath(filepath))
    if dirname not in args.include_paths:
        args.include_paths.append(dirname)


def mk_tmp_package_proj(args: argparse.Namespace):
    # Create CMakeLists.txt
    mk_tmp_file(f"{args.output_dir}/CMakeLists.txt",
                gen_cmakelist(target_name=args.package_name,
                              pyopendds_ldir=args.pyopendds_ld,
                              idl_files=args.input_files,
                              include_dirs=args.include_paths,
                              venv_path=os.environ['VIRTUAL_ENV']))

    # add args to the make command
    if args.make_opts == "":
        make_opts = []
    else:
        make_opts = args.make_opts.split(" ")

    # Run cmake to prepare the python to cpp bindings
    subprocess.run(['mkdir', '-p', 'build'], cwd=args.output_dir)
    subprocess_check_run(['cmake', '..'], cwd=f"{args.output_dir}/build")
    subprocess_check_run(['make'] + make_opts, cwd=f"{args.output_dir}/build")

    # Build the python IDL package
    itl_files = resolve_wildcard('*.itl', f'{args.output_dir}/build')
    subprocess_check_run(['itl2py',
                          '-o',
                          f"{args.package_name}_ouput",
                          f"{args.package_name}_idl",
                          *itl_files,
                          '--package-name',
                          f'py{args.package_name}'],
                         cwd=f"{args.output_dir}/build")

    # Install the python package py[package_name]
    tmp_env = os.environ.copy()
    tmp_env[f"{args.package_name}_idl_DIR"] = f"{os.path.abspath(args.output_dir)}/build"

    subprocess_check_run(['pip', 'install', '.'],
                         cwd=f"{args.output_dir}/build/{args.package_name}_ouput",
                         env=tmp_env)

    # Cleanup temporary folder
    if not args.user_defined_output:
        subprocess.run(['rm', '-r', args.output_dir])


def mk_tmp_file(pathname: str, content: str):
    file = open(pathname, 'w')
    file.write(content)
    file.close()


def run():
    parser = argparse.ArgumentParser(description='Generate and install IDL Python class(es) from IDL file(s).'
                                                 ' If no input file is given, all the idl files present in the current'
                                                 ' directory will be embed into the output package.')
    parser.add_argument('input_files', nargs='*',
                        help='the .idl source files')
    parser.add_argument('-p', '--package-name', metavar='',
                        help='the python generated package name '
                             '(default: the basename of the first input file)')
    parser.add_argument('-d', '--pyopendds-ld', metavar='',
                        help='the path to pyopendds project. You can also define PYOPENDDS_LD as environment variable')
    parser.add_argument('-o', '--output-dir', metavar='',
                        help='create a directory for the generated sources.')
    parser.add_argument('-i', '--include-paths', nargs='*', metavar='',
                        help='the include paths needed by the IDL files, if any')
    parser.add_argument('-m', '--make-opts', metavar='',
                        help='arguments passed to make')

    args = parser.parse_args()
    current_dir = os.getcwd()

    # Check if an environment is sourced
    if not in_virtualenv():
        if not prompt('No virtual environment seems to be sourced. Would you like to continue ?'):
            print("Aborting...")
            sys.exit(1)

    # Initialize include paths or convert directories names into absolute paths
    if not args.include_paths:
        args.__setattr__('include_paths', [])
    for idx, include_path in enumerate(args.include_paths):
        args.include_paths[idx] = os.path.realpath(include_path)

    # Convert file names into absolute filepath
    for idx, input_file in enumerate(args.input_files):
        abs_filepath = os.path.realpath(input_file)
        args.input_files[idx] = abs_filepath
        add_include_path(args, abs_filepath)

    # Discover all .idl files in the current dir if no input given
    if not args.input_files:
        for filename in os.listdir(current_dir):
            f = os.path.join(current_dir, filename)
            if os.path.isfile(f) and filename.lower().endswith('.idl'):
                args.input_files.append(f)
                add_include_path(args, f)
        if len(args.input_files) == 0:
            print("Error: no IDL file to compile in the current directory.")
            sys.exit(1)

    # Parse package name. If no name is given, the basename of the first .idl file will be taken
    if not args.package_name:
        args.__setattr__('package_name', os.path.splitext(os.path.basename(args.input_files[0]))[0])

    # Check the ouput_dir (default will be $CWD/temp)
    args.__setattr__('user_defined_output', True)
    if not args.output_dir:
        default_output_dir = f'pyidl-{args.package_name}-build'
        args.__setattr__('output_dir', f'{os.getcwd()}/{default_output_dir}')
        args.__setattr__('user_defined_output', False)
    else:
        output_dir_abspath = os.path.realpath(args.output_dir)
        if os.path.isdir(output_dir_abspath) and len(os.listdir(output_dir_abspath)) != 0:
            print(f"{output_dir_abspath} is not empty. Building and installing anyway...")
            # sys.exit(1)
    args.__setattr__('output_dir', os.path.realpath(args.output_dir))

    # Create the output directory if it does not exist
    if not os.path.exists(args.output_dir):
        subprocess.run(['mkdir', '-p', args.output_dir])

    # Check pyopendds include path (which is required in further CMake process)
    # Order of discovery is:
    #     1- Folder name or path given as input
    #     2- Environment variable named PYOPENDDS_LD
    #     1- Direct reference to include directory installed in pyopendds .egg archive (always successes)
    include_subpath = '/pyopendds/dev/include'
    if not args.pyopendds_ld:
        env_pyopendds_ld = os.getenv('PYOPENDDS_LD')
        if not env_pyopendds_ld:
            args.__setattr__('pyopendds_ld', extract_include_path_from_egg(args.output_dir))
        else:
            args.__setattr__('pyopendds_ld', f'{env_pyopendds_ld}{include_subpath}')
    else:
        args.__setattr__('pyopendds_ld', f'{args.pyopendds_ld}{include_subpath}')
    args.__setattr__('pyopendds_ld', os.path.realpath(args.pyopendds_ld))

    if not args.make_opts:
        args.__setattr__('make_opts', "")

    # Process generation and packaging
    mk_tmp_package_proj(args=args)
    sys.exit(0)


if __name__ == "__main__":
    run()
