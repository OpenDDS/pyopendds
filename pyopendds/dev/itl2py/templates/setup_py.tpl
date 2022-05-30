import os
import inspect
import sys
from pathlib import Path
from setuptools import setup, find_packages

import cmake_build_extension

from pyopendds.dev.util import get_include_path

keep_rpath = os.environ.get("KEEP_RPATH", "OFF")
python_root = Path(sys.prefix).resolve()
pyopendds_include = get_include_path()
build_type = os.environ.get("PYOPENDDS_BUILD_TYPE", "Release")
init_py = inspect.cleandoc(
  """
import cmake_build_extension as _cmake_build_extension
with _cmake_build_extension.build_extension_env():
    from .{{ native_package_name }} import *
"""
)

setup(
  name="{{ package_name }}",
  version="{{ package_version }}",
  packages=find_packages(),
  ext_modules=[
    cmake_build_extension.CMakeExtension(
      name="{{ native_package_name }}",
      install_prefix="{{ native_package_name }}",
      source_dir=".",
      write_top_level_init=init_py,
      cmake_configure_options=[
        f"-DPython3_ROOT_DIR={python_root}",
        "-DCALL_FROM_SETUP_PY:BOOL=ON",
        "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH:BOOL={keep_rpath}",
        f"-DPYOPENDDS_INCLUDE={pyopendds_include}",
      ],
      cmake_build_type=build_type,
    )
  ],
  cmdclass=dict(build_ext=cmake_build_extension.BuildExtension),
  install_requires=[
    "pyopendds",
    "cmake-build-extension",
  ],
)
