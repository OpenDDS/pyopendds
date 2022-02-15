import argparse
import glob
import os
import os.path
import shutil
import subprocess
import sys
from shlex import split

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
    files = glob.glob(os.path.join(dir_name, expr))
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
    root_path = os.path.realpath(os.path.join(script_path, '..', '..', '..'))
    include_dir = os.path.join(output_dir, 'include')
    sub_path = os.path.join('pyopendds', 'dev', 'include')

    if os.path.isfile(root_path) and root_path.lower().endswith('.egg'):
        with ZipFile(root_path, 'r') as zipObj:
            source_dir_path = os.path.join(output_dir, sub_path)
            for fileName in zipObj.namelist():
                if fileName.startswith(sub_path):
                    zipObj.extract(fileName, output_dir)
            subprocess.run(split(f"mv {source_dir_path} {include_dir}"))
            shutil.rmtree(os.path.join(output_dir, 'pyopendds'))
        return include_dir
    else:
        return os.path.join(root_path, sub_path)


def add_include_path(args: argparse.Namespace, filepath: str):
    dirname = os.path.dirname(os.path.realpath(filepath))
    if dirname not in args.include_paths:
        args.include_paths.append(dirname)


def mk_tmp_package_proj(args: argparse.Namespace):
    # Create CMakeLists.txt
    os.makedirs(args.build_dir, exist_ok=True)
    mk_tmp_file(os.path.join(args.build_dir, '..', 'CMakeLists.txt'),
                gen_cmakelist(target_name=args.package_name,
                              pyopendds_ldir=args.pyopendds_ld,
                              idl_files=args.input_files,
                              include_dirs=args.include_paths,
                              venv_path=os.environ['VIRTUAL_ENV']))

    # Run cmake to prepare the python to cpp bindings
    subprocess_check_run(split("cmake .."), cwd=args.build_dir)
    subprocess_check_run(split(f"make {args.make_opts}"), cwd=args.build_dir)

    # Build the python IDL package
    itl_files: list = resolve_wildcard('*.itl', args.build_dir)
    subprocess_check_run(split("itl2py -o{package_name}_ouput "
                               "{package_name}_idl {files} "
                               "--package-name py{package_name} "
                               "--package-version=\"{version}\"".format(package_name=args.package_name,
                                                                        files=' '.join(itl_files),
                                                                        version=args.package_version)),
                         cwd=args.build_dir)

    # Install the python package py[package_name]
    tmp_env = os.environ.copy()
    tmp_env[f"{args.package_name}_idl_DIR"] = args.build_dir

    subprocess_check_run(split(f"python3 setup.py bdist_wheel --dist-dir={args.dist_dir}"),
                         cwd=os.path.join(args.build_dir, f"{args.package_name}_ouput"),
                         env=tmp_env)

    if args.force_install:
        whl_list = glob.glob(os.path.join(args.dist_dir, f"py{args.package_name}*.whl"))
        if len(whl_list):
            package_path = whl_list[0]
            subprocess_check_run(split(f"pip install {package_path} --force-reinstall"),
                                 cwd=os.path.join(args.build_dir, f"{args.package_name}_ouput"),
                                 env=tmp_env)
        else:
            raise FileNotFoundError()

    # Cleanup temporary folder
    if not args.user_defined_output:
        shutil.rmtree(args.output_dir)


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
    parser.add_argument('-v', '--package-version', metavar='', default="0.0.0",
                        help="Package version")
    parser.add_argument('-d', '--pyopendds-ld', metavar='',
                        help='the path to pyopendds project. You can also define PYOPENDDS_LD as environment variable')
    parser.add_argument('-o', '--output-dir', metavar='',
                        help='create a directory for the generated sources.')
    parser.add_argument('-i', '--include-paths', nargs='*', metavar='',
                        help='the include paths needed by the IDL files, if any')
    parser.add_argument('-m', '--make-opts', metavar='',
                        help='arguments passed to make')
    parser.add_argument('--force-install', action='store_true',
                        help='install the generated package')

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
        args.__setattr__('output_dir', os.path.join(os.getcwd(), 'build'))
        args.__setattr__('build_dir', os.path.join(os.getcwd(), 'build', default_output_dir, 'build'))
        args.__setattr__('dist_dir', os.path.join(os.getcwd(), 'dist'))
        args.__setattr__('user_defined_output', False)
    else:
        args.output_dir = os.path.realpath(args.output_dir)
        if os.path.isdir(args.output_dir) and len(os.listdir(args.output_dir)) != 0:
            print(f"{args.output_dir} is not empty. Building and installing anyway...")
            # sys.exit(1)
        args.__setattr__('build_dir', os.path.join(args.output_dir, 'build'))
        args.__setattr__('dist_dir', os.path.join(args.output_dir, 'dist'))


    # Create the output directory if it does not exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)

    # Check pyopendds include path (which is required in further CMake process)
    # Order of discovery is:
    #     1- Folder name or path given as input
    #     2- Environment variable named PYOPENDDS_LD
    #     1- Direct reference to include directory installed in pyopendds .egg archive (always successes)
    include_subpath = os.path.join('pyopendds', 'dev', 'include')
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
