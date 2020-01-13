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
    argparser.add_argument('--default-encoding',
        type=str, default='utf_8',
        help='Default encoding of strings. By default this is UTF-8.')
    argparser.add_argument('--dry-run', action='store_true',
        help='Don\'t create any files or directories, print out what would be done.')
    argparser.add_argument('--dump-ast', action='store_true',
        help='Print the AST before processing it')
    args = argparser.parse_args()

    # Fill in any missing arguments
    if args.package_name is None:
        if len(args.itl_files) > 1:
            sys.exit('--package-name is required when using multiple ITL files')
        args.package_name = 'py' + args.itl_files[0].stem
    if args.native_package_name is None:
        args.native_package_name = '_' + args.package_name

    # Generate The Python Package
    generate(vars(args))


if __name__ == "__main__":
    main()
