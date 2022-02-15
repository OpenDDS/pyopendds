from pathlib import Path
from setuptools import setup
from pyopendds.dev.cmake import CMakeWrapperExtension, CMakeWrapperBuild

setup(
    name='pyopendds',
    packages=['pyopendds'],
    ext_modules=[CMakeWrapperExtension(
        name='_pyopendds',
        cmakelists_dir='pyopendds/ext',
        extra_vars={
            'PYOPENDDS_INCLUDE':
                Path(__file__).resolve().parent / 'pyopendds/dev/include',
        },
    )],
    cmdclass={'build_ext': CMakeWrapperBuild},
)
