import argparse
import glob
import os
import os.path
import shutil
import subprocess
import sys
from shlex import split
import re

from zipfile import ZipFile
from .gencmakefile import gen_cmakelist, gen_cmakeconfig


def get_base_prefix_compat():
    return (
        getattr(sys, "base_prefix", None)
        or getattr(sys, "real_prefix", None)
        or sys.prefix
    )


def in_virtualenv():
    return get_base_prefix_compat() != sys.prefix


def virtualenv_dir():
    return sys.prefix


def resolve_wildcard(expr, dir_name) -> list:
    files = glob.glob(os.path.join(dir_name, expr))
    rem_part = len(dir_name) + 1
    return list(map(lambda s: s[rem_part:], files))


def subprocess_check_run(commands: list, cwd: str, env=None, description: str = ""):
    try:
        subprocess.run(commands, cwd=cwd, check=True, env=env)
    except subprocess.CalledProcessError as err:
        print()  # print blank line
        if description:
            print(description)

        print(
            f"An error occured with the following command:\n"
            f"\tCWD: {cwd}\n"
            f"\tCMD: {' '.join(err.cmd)}\n"
            f"Exiting pyidl with status {err.returncode}."
        )
        sys.exit(err.returncode)


def extract_include_path_from_egg(output_dir: str):
    # potentially is into a egg archive
    script_path = os.path.dirname(os.path.realpath(__file__))
    root_path = os.path.realpath(os.path.join(script_path, "..", "..", ".."))
    include_dir = os.path.join(output_dir, "include")
    sub_path = os.path.join("pyopendds", "dev", "include")

    if os.path.isfile(root_path) and root_path.lower().endswith(".egg"):
        with ZipFile(root_path, "r") as zipObj:
            source_dir_path = os.path.join(output_dir, sub_path)
            for fileName in zipObj.namelist():
                if fileName.startswith(sub_path):
                    zipObj.extract(fileName, output_dir)
            subprocess.run(split(f"mv {source_dir_path} {include_dir}"))
            shutil.rmtree(os.path.join(output_dir, "pyopendds"))
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

    mk_tmp_file(
        os.path.join(args.build_dir, "..", "CMakeLists.txt"),
        gen_cmakelist(
            target_name=args.package_name,
            pyopendds_ldir=args.pyopendds_ld,
            idl_files=args.input_files,
            include_dirs=args.include_paths,
        ),
    )
    mk_tmp_file(
        os.path.join(
            args.build_dir, "..", "{}_idlConfig.cmake.in".format(args.package_name)
        ),
        gen_cmakeconfig(
            target_name=args.package_name,
            pyopendds_ldir=args.pyopendds_ld,
            idl_files=args.input_files,
            include_dirs=args.include_paths,
        ),
    )

    """
        cd buildIdl/
        cd build/
        cmake ..
        DESTDIR=prefix make install
        itl2py -o DFApplication DFApplication_idl opendds_generated/*.itl --package-name pyDFApplication
        VERBOSE=1 DFApplication_idl_DIR=../prefix/usr/local/share/cmake/DFApplication_idl/ python setup.py bdist_wheel
    """

    """
        cd buildIdl/
        cd build/
        cmake ..
    """
    # Run cmake to prepare the python to cpp bindings
    if in_virtualenv():
        subprocess_check_run(split(f"cmake -DCMAKE_INSTALL_PREFIX={virtualenv_dir()} .."), cwd=args.build_dir)
        # DESTDIR=prefix make install
        subprocess_check_run(
            split(f"make install {args.make_opts}"), cwd=args.build_dir
        )
    else:
        subprocess_check_run(split(f"cmake .."), cwd=args.build_dir)
        # DESTDIR=prefix make install
        subprocess_check_run(
            split(f"make install {args.make_opts} DESTDIR=prefix"), cwd=args.build_dir
        )

    if in_virtualenv():
        prefix_dir = virtualenv_dir()
        install_dir = os.path.join(
            prefix_dir,
            "share",
            "cmake",
            "{package_name}_idl".format(package_name=args.package_name),
        )

    else:
        prefix_dir = os.path.join(args.build_dir, "prefix")
        install_dir = os.path.join(
            prefix_dir,
            "usr",
            "local",
            "share",
            "cmake",
            "{package_name}_idl".format(package_name=args.package_name),
        )
    """ itl2py -o DFApplication DFApplication_idl opendds_generated/*.itl --package-name pyDFApplication """
    # Build the python IDL package
    itl_files: list = resolve_wildcard("opendds_generated/*.itl", args.build_dir)
    subprocess_check_run(
        split(
            "itl2py -o{package_name} "
            "{package_name}_idl {files} "
            "--package-name py{package_name} "
            '--package-version="{version}" '
            "--idl-library-build-dir={lib_dir} ".format(
                package_name=args.package_name,
                files=" ".join(itl_files),
                version=args.package_version,
                build_dir=args.build_dir,
                lib_dir=install_dir,
            )
        ),
        cwd=args.build_dir,
    )

    """ VERBOSE=1 DFApplication_idl_DIR=../prefix/usr/local/share/cmake/DFApplication_idl/ \
    python setup.py bdist_wheel """
    # Install the python package py[package_name]
    os.unlink(
        os.path.join(args.build_dir, f"{args.package_name}_idlConfig.cmake")
    )
    python_build_dir = os.path.join(args.build_dir, args.package_name)
    # tmp_env = os.environ.copy()
    # tmp_env["{package_name}_idl_DIR".format(package_name=args.package_name)] = cmake_config_dir
    cmd = "{exe} setup.py bdist_wheel --dist-dir={dist_dir}".format(
        exe=sys.executable, package_name=args.package_name, dist_dir=args.dist_dir
    )
    # subprocess_check_run(split(cmd), cwd=python_build_dir, env=tmp_env)
    subprocess_check_run(split(cmd), cwd=python_build_dir)

    if args.force_install:
        whl_list = glob.glob(os.path.join(args.dist_dir, f"py{args.package_name}*.whl"))
        if len(whl_list):
            package_path = whl_list[0]
            subprocess_check_run(
                split(f"pip install {package_path} --force-reinstall --no-deps"),
                cwd=args.build_dir)
        else:
            raise FileNotFoundError()

    # Cleanup temporary folder
    if not args.user_defined_output:
        shutil.rmtree(args.output_dir)


def mk_tmp_file(pathname: str, content: str):
    file = open(pathname, "w")
    file.write(content)
    file.close()


def process_idl_file_list(idl_list_filename: str) -> list:    
    with open(idl_list_filename, "r") as fh:
        raw_idl_list = fh.read()
        idl_list = re.split("\s+", raw_idl_list)
        
        idl_filenames = []
        for idl_filename in idl_list:
            idl_filenames.append( os.path.expandvars(idl_filename) )

        return idl_filenames


def run():
    parser = argparse.ArgumentParser(
        description="Generate and install IDL Python class(es) from IDL file(s)."
        " If no input file is given, all the idl files present in the current"
        " directory will be embed into the output package."
    )
    parser.add_argument("input_files", nargs="*", help="the .idl source files")

    parser.add_argument("-I", "--input-filelist", default=False, help="list of .idl source files")

    parser.add_argument(
        "-p",
        "--package-name",
        metavar="",
        help="the python generated package name "
        "(default: the basename of the first input file)",
    )
    parser.add_argument(
        "-v", "--package-version", metavar="", default="0.0.0", help="Package version"
    )
    parser.add_argument(
        "-d",
        "--pyopendds-ld",
        metavar="",
        help="the path to pyopendds project. You can also define PYOPENDDS_LD as environment variable",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        metavar="",
        help="create a directory for the generated sources.",
    )
    parser.add_argument(
        "-i",
        "--include-paths",
        nargs="*",
        metavar="",
        help="the include paths needed by the IDL files, if any",
    )
    parser.add_argument(
        "-m", "--make-opts", metavar="", help="arguments passed to make"
    )
    parser.add_argument(
        "--force-install", action="store_true", help="install the generated package"
    )
    parser.add_argument(
        "-y", "--yes", action="store_true", help="respond to yes to prompt (deprecated)"
    )

    args = parser.parse_args()
    current_dir = os.getcwd()

    # Check if an environment is sourced
    if in_virtualenv():
        os.environ["KEEP_RPATH"] = "true"

    # Initialize include paths or convert directories names into absolute paths
    if not args.include_paths:
        args.__setattr__("include_paths", [])
    for idx, include_path in enumerate(args.include_paths):
        args.include_paths[idx] = os.path.realpath(include_path)

    # Convert file names into absolute filepath
    for idx, input_file in enumerate(args.input_files):
        abs_filepath = os.path.realpath(input_file)
        args.input_files[idx] = abs_filepath
        add_include_path(args, abs_filepath)


    # Allow only one input method for IDL files
    if not args.input_files and not args.input_filelist:
        print("Error: Cannot add IDLs from pyidl arguments and from an input file source (-I)")
        sys.exit(1)
    
    input_idl_filenames = None

    # List IDLs from file
    if args.input_filelist:
        idl_source_filename = os.path.join(current_dir, args.input_filelist)
        print("List IDLs from:", idl_source_filename)
        # extract list of filenames
        input_idl_filenames = process_idl_file_list(idl_source_filename)
    # List IDLs from arguments
    elif args.input_files:
        input_idl_filenames = args.input_files
    else:
        raise Exception("Error while parsing the list of IDLs filenames")

    # Expand patterns for each filename
    input_idl_filenames_ext = []
    for filename in input_idl_filenames:
        filenames = glob.glob(filename)
        input_idl_filenames_ext.extend( filenames )

    args.input_files = input_idl_filenames_ext

    if len(args.input_files) == 0:
        print("Error: no IDL files provided.")
        sys.exit(1)

    # Parse package name. If no name is given, the basename of the first .idl file will be taken
    if not args.package_name:
        args.__setattr__(
            "package_name", os.path.splitext(os.path.basename(args.input_files[0]))[0]
        )

    # Check the ouput_dir (default will be $CWD/temp)
    args.__setattr__("user_defined_output", True)
    if not args.output_dir:
        default_output_dir = f"pyidl-{args.package_name}-build"
        args.__setattr__("output_dir", os.path.join(os.getcwd(), "build"))
        args.__setattr__(
            "build_dir", os.path.join(os.getcwd(), "build", default_output_dir, "build")
        )
        args.__setattr__("dist_dir", os.path.join(os.getcwd(), "dist"))
        args.__setattr__("user_defined_output", False)
    else:
        args.output_dir = os.path.realpath(args.output_dir)
        if os.path.isdir(args.output_dir) and len(os.listdir(args.output_dir)) != 0:
            print(f"{args.output_dir} is not empty. Building and installing anyway...")
            # sys.exit(1)
        args.__setattr__("build_dir", os.path.join(args.output_dir, "build"))
        args.__setattr__("dist_dir", os.path.join(args.output_dir, "dist"))

    # Create the output directory if it does not exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)

    # Check pyopendds include path (which is required in further CMake process)
    # Order of discovery is:
    #     1- Folder name or path given as input
    #     2- Environment variable named PYOPENDDS_LD
    #     1- Direct reference to include directory installed in pyopendds .egg archive (always successes)
    include_subpath = os.path.join("pyopendds", "dev", "include")
    if not args.pyopendds_ld:
        env_pyopendds_ld = os.getenv("PYOPENDDS_LD")
        if not env_pyopendds_ld:
            args.__setattr__(
                "pyopendds_ld", extract_include_path_from_egg(args.output_dir)
            )
        else:
            args.__setattr__("pyopendds_ld", f"{env_pyopendds_ld}{include_subpath}")
    else:
        args.__setattr__("pyopendds_ld", f"{args.pyopendds_ld}{include_subpath}")
    args.__setattr__("pyopendds_ld", os.path.realpath(args.pyopendds_ld))

    if not args.make_opts:
        args.__setattr__("make_opts", "")

    # Process generation and packaging
    mk_tmp_package_proj(args=args)
    sys.exit(0)


if __name__ == "__main__":
    run()
