from pathlib import Path
from setuptools import setup, find_packages
from pyopendds.dev.cmake import CMakeWrapperExtension, CMakeWrapperBuild
import distutils.command.sdist
import sys


ext_package = {'pyopendds': ['ext/*']}
setup(
    packages=find_packages(),
    ext_modules=[CMakeWrapperExtension(
        name='_pyopendds',
        cmakelists_dir='pyopendds/ext',
        extra_vars={
            'PYOPENDDS_INCLUDE':
                Path(__file__).resolve().parent / 'pyopendds/dev/include',
        },
    )],
    cmdclass={'build_ext': CMakeWrapperBuild},
    entry_points={
        'console_scripts': [
            'itl2py=pyopendds.dev.itl2py.__main__:main',
            'pyidl=pyopendds.dev.pyidl.__main__:run',
        ],
    },
    package_data={
        'pyopendds':['ext/*'] if 'sdist' in sys.argv else [],
        'pyopendds':['ext/*'] if 'bdist_rpm' in sys.argv else [],
        'pyopendds.dev': [
            'include/pyopendds/*',
        ],
        'pyopendds.dev.itl2py': [
            'templates/*', 
        ],

    },
    install_requires=[
        'Jinja2'
    ],
)
