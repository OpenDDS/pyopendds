from setuptools import setup, find_packages

from pyopendds.dev.cmake import CMakeWrapperExtension, CMakeWrapperBuild

setup(
    packages=find_packages(),
    ext_modules=[CMakeWrapperExtension(
        name='_pyopendds',
        cmakelists_dir='pyopendds/ext',
    )],
    cmdclass={'build_ext': CMakeWrapperBuild},
    scripts=['scripts/itl2py'],
)
