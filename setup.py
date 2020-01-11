from setuptools import setup, find_packages

from pyopendds.dev.cmake import *

setup(
  name = 'pyopendds',
  version = '0.0.0', # TODO: Automate Versioning
  description = 'Python Bindings for OpenDDS',
  classifiers = [
    'License :: OSI Approved :: MIT License',
  ],
  # TODO: Fill Out More MetaData
  packages = find_packages(),
  ext_modules = [CMakeWrapperExtension(
    name = '_pyopendds',
    cmakelists_dir='pyopendds/ext',
  )],
  cmdclass = {'build_ext': CMakeWrapperBuild},
  scripts = ['scripts/itl2py']
)
