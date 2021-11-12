import sys
from argparse import ArgumentParser
from pathlib import Path

from .generate import generate


def main():
    # Parse Arguments
    argparser = ArgumentParser(description='ITL to Python Mapping Generator')
    argparser.add_argument('idl_library_cmake_name',
        metavar='IDL_LIBRARY_CMAKE_NAME', type=str,
        help='Name of the exported CMake library to use.')
    argparser.add_argument('itl_files',
        metavar='ITL_FILE', type=Path, nargs='+',
        help='Files that contain the types definitions.')
    argparser.add_argument('-o', '--output',
        type=Path, default=Path('.'),
        help='Destination directory. The current directory by default.')
    argparser.add_argument('-n', '--package-name',
        type=str,
        help='''\
Name of the Python package to create. If there is only one ITL file, then by
default this will be \'py\' and the name of the ITL file with the .itl
extension (my_types.itl -> pymy_types). If there are are multiple ITL files,
then this option becomes required.''')
    argparser.add_argument('--native-package-name',
        type=str,
        help='''\
Name of the native Python extension package to create. By default this is \'_\'
and the name of the Python package.''')
    argparser.add_argument('--idl-library-build-dir',
        metavar='IDL_LIBRARY_BUILD_DIR', type=Path,
        help='''\
Location of the CMake config file to use. By default this will be the location
of all the input ITL files if they are in the same location. If they are not or
the exepcted config file is not there, then this option becomes required.'''),
    argparser.add_argument('--default-encoding',
        type=str, default='utf_8',
        help='Default encoding of strings. By default this is UTF-8.')
    argparser.add_argument('--dry-run', action='store_true',
        help='Don\'t create any files or directories, print out what would be done.')
    argparser.add_argument('--dump-ast', action='store_true',
        help='Print the AST before processing it.')
    argparser.add_argument('--just-dump-ast', action='store_true',
        help='Just print the AST.')
    args = argparser.parse_args()

    # Fill in any missing arguments
    if args.package_name is None:
        if len(args.itl_files) > 1:
            sys.exit('--package-name is required when using multiple ITL files')
        args.package_name = 'py' + args.itl_files[0].stem
    if args.native_package_name is None:
        args.native_package_name = '_' + args.package_name
    if args.idl_library_build_dir is None:
        args.idl_library_build_dir = args.itl_files[0].resolve().parent
        for path in args.itl_files[1:]:
            if path.resolve().parent != args.idl_library_build_dir:
                sys.exit('''\
--idl-library-build-dir is required when ITL files are in different directories''')
    else:
        # CMake will freak out if there are DOS-style slashes in the path
        args.idl_library_build_dir = args.idl_library_build_dir.resolve().as_posix()
    config_filename = '{}Config.cmake'.format(args.idl_library_cmake_name)
    config_path = args.idl_library_build_dir / config_filename
    if not config_path.is_file():
        sys.exit('''\
Native IDL library CMake config file {} does not exist, please pass the
directory for it (where cmake was ran) using --idl-library-build-dir'''.format(config_path))

    # Generate The Python Package
    generate(vars(args))


if __name__ == "__main__":
    main()
