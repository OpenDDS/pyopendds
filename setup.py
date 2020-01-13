from setuptools import setup, find_packages

from pyopendds.dev.cmake import CMakeWrapperExtension, CMakeWrapperBuild

setup(
    packages=find_packages(),
    ext_modules=[CMakeWrapperExtension(
        name='_pyopendds',
        cmakelists_dir='pyopendds/ext',
    )],
    cmdclass={'build_ext': CMakeWrapperBuild},
    entry_points={
        'console_scripts': [
            'itl2py=pyopendds.dev.itl2py.__main__:main',
        ],
    },
    package_data={'pyopendds.dev.itl2py': ['templates/*']},
    install_requires=[
        'jinja2',
    ],
)
