import sys
import os
import inspect
from pathlib import Path
from setuptools import setup
from setuptools import find_packages

import cmake_build_extension

build_type = os.environ.get('PYOPENDDS_BUILD_TYPE', 'Release')
init_py = inspect.cleandoc(
    """
    import cmake_build_extension as _cmake_build_extension
    with _cmake_build_extension.build_extension_env():
        from ._pyopendds import *
    """
)

setup(
    packages=find_packages(),
    ext_modules=[
        cmake_build_extension.CMakeExtension(
            name='_pyopendds',
            install_prefix='_pyopendds',
            source_dir='pyopendds/ext',
            write_top_level_init=init_py,
            cmake_configure_options=[
                f'-DPython3_ROOT_DIR={Path(sys.prefix)}',
                '-DCALL_FROM_SETUP_PY:BOOL=ON',
                '-DPYOPENDDS_INCLUDE='
                + str(Path(__file__).resolve().parent / 'pyopendds/dev/include'),
            ],
            cmake_build_type=build_type,
        )
    ],
    cmdclass=dict(build_ext=cmake_build_extension.BuildExtension),
    entry_points={
        'console_scripts': [
            'itl2py=pyopendds.dev.itl2py.__main__:main',
            'pyidl=pyopendds.dev.pyidl.__main__:run',
        ],
    },
    package_data={
        'pyopendds.dev': [
            'include/pyopendds/*',
        ],
        'pyopendds.dev.itl2py': [
            'templates/*',
        ],
        'pyopendds.dev.pyidl': [
            'templates/*',
        ]
    },
    install_requires=[
        'jinja2',
        'cmake',
        'cmake-build-extension'
    ]
)
