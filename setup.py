from setuptools import setup

from pyopendds_dev.cmake import *

setup(
  name = 'pyopendds',
  version = '0.0.0', # TODO: Automate Versioning
  description = 'Python Bindings for OpenDDS',
  classifiers = [
    'License :: OSI Approved :: MIT License',
  ],
  # TODO: Fill Out More MetaData
  py_modules = ['pyopendds', 'pyopendds_dev'],
  ext_modules = [CMakeWrapperExtension(
    name = '_pyopendds',
    cmakelists_dir='.',
  )],
  cmdclass = {'build_ext': CMakeWrapperBuild},
  scripts = ['itl2py']
)
