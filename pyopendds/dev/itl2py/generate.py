import sys
from pathlib import Path
from typing import List
import codecs
import json

from jinja2 import Environment, PackageLoader

from .itl import parse_itl
from .ast import get_ast, Module
from .Output import Output
from .PythonOutput import PythonOutput
from .CppOutput import CppOutput


def parse_itl_files(itl_files: List[Path]) -> Module:
    '''Read and parse a list of ITL file paths, collecting the results and
    return an assembled AST.
    '''

    types = {}
    for itl_file in itl_files:
        with itl_file.open() as f:
            parse_itl(types, json.load(f))
    return get_ast(types)


class PackageOutput(Output):
    '''Wraps the other Outputs and manages build files for the Python package
    '''

    def __init__(self, context: dict):
        super().__init__(context, context['output'], {
            'CMakeLists.txt': 'CMakeLists.txt',
            'setup.py': 'setup.py',
        })
        self.pyout = PythonOutput(context, context['package_name'])
        self.cppout = CppOutput(context)

    def visit_root_module(self, root_module):
        if self.context['dump_ast']:
            print(repr(root_module))
            super().visit_root_module(root_module)
        self.pyout.visit_root_module(root_module)
        self.cppout.visit_root_module(root_module)

    def write(self):
        super().write()
        self.pyout.write()
        self.cppout.write()

    def visit_struct(self, struct_type):
        print(repr(struct_type))
        for field_node in struct_type.fields.values():
            print('    ', repr(field_node))

    def visit_enum(self, enum_type):
        print(repr(enum_type))
        for name, value in enum_type.members.items():
            print('    ', name, ':', value)


def generate(context: dict) -> None:
    '''Generate a Python IDL binding package given a dict of arguments. The
    arguments are the following:
        - idl_library_cmake_name
        - itl_files
        - output
        - package_name
        - native_package_name
        - default_encoding
        - dry_run
        - dump_ast
    '''

    try:
        codecs.lookup(context['default_encoding'])
    except LookupError:
        sys.exit('Invalid Python codec: "{}"'.format(context['default_encoding']))

    context['jinja_loader'] = PackageLoader('pyopendds.dev.itl2py', 'templates')
    context['jinja'] = Environment(
        loader=context['jinja_loader'],
    )

    out = PackageOutput(context)
    out.visit_root_module(parse_itl_files(context['itl_files']))
    out.write()
