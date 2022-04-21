import cmake_build_extension as _cmake_build_extension

with _cmake_build_extension.build_extension_env():
    from ._pyopendds import *
