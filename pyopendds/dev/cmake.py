'''CMake Wrapper for setuptools Based on
https://martinopilia.com/posts/2018/09/15/building-python-extension.html
'''

import sys
from pathlib import Path
import subprocess

from distutils.errors import DistutilsSetupError
from setuptools import Extension
from setuptools.command.build_ext import build_ext


class CMakeWrapperExtension(Extension):
    def __init__(self, name,
            cmakelists_dir='.',
            cmake_command='cmake',
            cmake_build_type='Debug',
            extra_vars={},
            **kw):
        Extension.__init__(self, name, sources=[], **kw)
        self.cmakelists_dir = Path(cmakelists_dir).resolve()
        self.cmake_command = cmake_command
        self.cmake_build_type = cmake_build_type
        self.extra_vars = extra_vars

    def cmake(self, args, cwd=Path()):
        '''CMake Command Wrapper Function
        '''
        command = [self.cmake_command] + args
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
                'Could not run "{}": {}'.format(
                    ' '.join(command), str(os_error)))
        except subprocess.CalledProcessError as return_code_error:
            raise DistutilsSetupError(
                '"{}" returned non-zero result: {}'.format(
                    ' '.join(command), return_code_error.returncode))

    def get_extra_vars(self):
        return ['-D{}={}'.format(k, v) for k, v in self.extra_vars.items()]


class CMakeWrapperBuild(build_ext):
    def build_extensions(self):
        # Make sure build directory exists
        build_temp = Path(self.build_temp)
        build_temp.mkdir(parents=True, exist_ok=True)

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
            ext.cmake(
                [
                    str(ext.cmakelists_dir),
                    '-DCMAKE_BUILD_TYPE=' + ext.cmake_build_type,
                    '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(
                        ext.cmake_build_type.upper(), extdir),
                    '-DPYOPENDDS_NATIVE_FILENAME=' + native_filename,
                    '-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY_{}={}'.format(
                        ext.cmake_build_type.upper(), str(build_temp)),
                ] + ext.get_extra_vars(),
                build_temp,
            )

            # Build
            ext.cmake(['--build', '.', '--config', ext.cmake_build_type], build_temp)


def get_include_path() -> Path:
    return Path(__file__).resolve().parent / 'include'
