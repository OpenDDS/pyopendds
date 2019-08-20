'''PyOpenDDS Setup
Tells Python how to build PyOpenDDS using CMake and install it.
'''

import sys
import os
from pathlib import Path
import subprocess

from distutils.errors import DistutilsSetupError
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

# TODO: Make these options again
cmake_command = 'cmake'
build_type = 'Debug'

def cmake(args, cwd=Path()):
  '''CMake Command Wrapper Function
  '''
  command = [cmake_command] + args
  try:
    subprocess.run(
      command,
      check=True,
      cwd=str(cwd),
      stdout=sys.stdout,
      stderr=sys.stderr,
    )
  except OSError as os_error:
    raise DistutilsSetupError(
      'Could not run "{}": {}' \
        .format(
          ' '.join(command),
          str(os_error),
        )
    )
  except subprocess.CalledProcessError as return_code_error:
    raise DistutilsSetupError(
      '"{}" returned non-zero result: {}' \
        .format(
          ' '.join(command),
          return_code_error.returncode,
        )
    )

# CMake Wrapper Based on
# https://martinopilia.com/posts/2018/09/15/building-python-extension.html
class CMakeWrapperExtension(Extension):
  def __init__(self, name, cmakelists_dir='.', **kw):
    Extension.__init__(self, name, sources=[], **kw)
    self.cmakelists_dir = Path(cmakelists_dir).resolve()

class CMakeWrapperBuild(build_ext):
  def build_extensions(self):
    # Make sure we can run CMake
    cmake(['--version'])

    # Make sure build directory exists
    if not os.path.exists(self.build_temp):
      os.makedirs(self.build_temp)

    # Build Each Extension
    for ext in self.extensions:
      # Get Location
      extdir = Path(self.get_ext_fullpath(ext.name)).parent.resolve()

      # We need to give the name Python is expecting to CMake
      try:
        native_filename = ext._file_name
      except AttributeError:
        raise DistutilsSetupError(
          'PLEASE REPORT THIS ERROR IF IT OCCURS: '
          'Extension does not have _file_name!'
        )

      # Configure
      cmake(
        [
          str(ext.cmakelists_dir),
          '-DCMAKE_BUILD_TYPE=' + build_type,
          '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(
            build_type.upper(), extdir),
          '-DPYOPENDDS_NATIVE_FILENAME=' + native_filename,
          '-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY_{}={}'.format(
            build_type.upper(), self.build_temp),
          '-DPYTHON_EXECUTABLE=' + sys.executable,
        ],
        self.build_temp,
      )

      # Build
      cmake(['--build', '.', '--config', build_type], self.build_temp)

_pyopendds = CMakeWrapperExtension(
  name = '_pyopendds',
  cmakelists_dir='.',
)

setup(
  name = 'pyopendds',
  version = '0.0.0', # TODO: Automate Versioning
  description = 'Python Bindings for OpenDDS',
  classifiers = [
    'License :: OSI Approved :: MIT License',
  ],
  # TODO: Fill Out More MetaData
  py_modules = ['pyopendds'],
  ext_modules = [_pyopendds],
  cmdclass = {'build_ext': CMakeWrapperBuild},
)
