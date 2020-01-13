from setuptools import setup, find_packages

from pyopendds.dev.cmake import CMakeWrapperExtension, CMakeWrapperBuild


setup(
    name='{{ package_name }}',
    packages=find_packages(),
    ext_modules=[CMakeWrapperExtension(
        name='{{ native_package_name }}',
        cmakelists_dir='.',
    )],
    cmdclass={'build_ext': CMakeWrapperBuild},
)
