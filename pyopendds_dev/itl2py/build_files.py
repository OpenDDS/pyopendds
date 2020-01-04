from pathlib import Path

def get_setup_py(python_module_name, native_module_name):
    return '''\
from setuptools import setup

from pyopendds_dev.cmake import *

setup(
    name = \'''' + python_module_name + '''\',
    py_modules = [\'''' + python_module_name + '''\'],
    ext_modules = [CMakeWrapperExtension(
        name = \'''' + native_module_name + '''\',
        cmakelists_dir='.',
    )],
    cmdclass = {'build_ext': CMakeWrapperBuild},
)
'''

def write_setup_py(output_dir: Path,
        python_module_name: str, native_module_name: str,
        filename: str='setup.py'):
    (output_dir / filename).write_text(
        get_setup_py(python_module_name, native_module_name))

def get_cmakelists_txt(native_module_name: str, idl_library_name: str):
    return '''\
cmake_minimum_required(VERSION 3.12)
project(''' + native_module_name + ''')

find_package(Python3 COMPONENTS Development REQUIRED)
find_package(OpenDDS REQUIRED)
find_package(''' + idl_library_name + ''' REQUIRED)

add_library(''' + native_module_name + ''' SHARED ''' + native_module_name + '''.cpp)
target_link_libraries(''' + native_module_name + ''' PRIVATE Python3::Python)
target_link_libraries(''' + native_module_name + ''' PRIVATE ''' + idl_library_name + ''')

# Set filename to exactly what Python is expecting
set_target_properties(''' + native_module_name + ''' PROPERTIES
  PREFIX ""
  LIBRARY_OUTPUT_NAME ${PYOPENDDS_NATIVE_FILENAME}
  SUFFIX ""
)
'''

def write_cmakelists_txt(output_dir: Path,
        native_module_name: str, idl_library_name: str,
        filename: str='CMakeLists.txt'):
    (output_dir / filename).write_text(
        get_cmakelists_txt(native_module_name, idl_library_name))
