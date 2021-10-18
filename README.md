# PyOpenDDS

[![](https://github.com/oci-labs/pyopendds/workflows/pyopendds/badge.svg)](
  https://github.com/oci-labs/pyopendds/actions?query=workflow%3Apyopendds)

Python Bindings for [OpenDDS](https://github.com/objectcomputing/OpenDDS).

This project is still a work in progress! It currently only supports what is
necessary for `tests/basic_test` and little else. See the GitHub issues for
limitations.

## Requirements

- Currently only Linux has been tested, but macOS should work and Windows might
  work.
- Python >= 3.7
  - This uses the C API of CPython, so PyPy or any other Python implementation
    is not supported.
- OpenDDS >= 3.16
- CMake >= 3.12
- A C++14 Compiler

## Building PyOpenDDS and Running the Basic Test

Once `$DDS_ROOT/setenv.sh` has been sourced or the equivalent, run the commands
below in this directory.

```sh
# Build and Install PyOpenDDS
pip install .

# Build Basic Test
cd tests/basic_test
mkdir build
cd build
cmake ..
make

# Build and Install Basic Test Python Type Support
itl2py -o basic_output basic_idl basic.itl
cd basic_output
pip install .

# Run Basic Test
cd ../..
bash run_test.sh
```
