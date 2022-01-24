from pathlib import Path
from setuptools import setup, find_packages
from glob import glob
from pyopendds.dev.cmake import CMakeWrapperExtension, CMakeWrapperBuild
import distutils.command.sdist
import sys
# class SdistCommand(distutils.command.sdist.sdist):
#     def run(self):
#         # 'filelist' contains the list of files that will make up the
#         # manifest
#         self.filelist = FileList()

#         # Run sub commands
#         for cmd_name in self.get_sub_commands():
#             self.run_command(cmd_name)

#         # Do whatever it takes to get the list of files to process
#         # (process the manifest template, read an existing manifest,
#         # whatever).  File list is accumulated in 'self.filelist'.
#         self.get_file_list()
#         # If user just wanted us to regenerate the manifest, stop now.
#         if self.manifest_only:
#             return

#         # Otherwise, go ahead and create the source distribution tarball,
#         # or zipfile, or whatever.
#         self.make_distribution()

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
