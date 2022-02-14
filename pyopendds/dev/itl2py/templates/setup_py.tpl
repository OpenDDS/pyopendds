from setuptools import setup, find_packages

from pyopendds.dev.cmake import \
    CMakeWrapperExtension, CMakeWrapperBuild, get_include_path


setup(
    name='{{ package_name }}',
    packages=find_packages(),
    ext_modules=[CMakeWrapperExtension(
        name='{{ native_package_name }}',
        cmakelists_dir='.',
        extra_vars={
            'PYOPENDDS_INCLUDE': get_include_path(),
        },
    )],
    cmdclass={'build_ext': CMakeWrapperBuild},
    install_requires=[
        'pyopendds',
    ],
)
