# PyOpenDDS

[![](https://github.com/oci-labs/pyopendds/workflows/pyopendds/badge.svg)](
https://github.com/oci-labs/pyopendds/actions?query=workflow%3Apyopendds)

PyOpenDDS is a framework for using
[OpenDDS](https://github.com/objectcomputing/OpenDDS) from Python. It has the goal of providing the standard full DDS
API in OpenDDS in a Pythonic form.

This project is still a work in progress though. It currently only supports what is necessary for `tests/basic_test` and
little else. See the GitHub issues for the current status of the limitations.

## Requirements

- Tested on Linux, macOS, and Windows
- CPython >= 3.7
    - This uses the C API of CPython, so other Python implementations like PyPy are not offically supported.
- OpenDDS >= 3.16
- CMake >= 3.12
- A C++14 Compiler

## Building PyOpenDDS and Running the Basic Test

Once `$DDS_ROOT/setenv.sh` has been sourced or the equivalent, run the commands below in this directory.

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
