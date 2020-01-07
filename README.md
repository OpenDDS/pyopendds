# PyOpenDDS

[![](https://github.com/iguessthislldo/pyopendds/workflows/pyopendds/badge.svg)](
  https://github.com/iguessthislldo/pyopendds/actions?query=workflow%3Apyopendds)

Python Bindings for [OpenDDS](https://github.com/objectcomputing/OpenDDS).

**WARNING: This project is still a work in progress!**

## Requirements

- Python >= 3.7
  - This uses the C API of CPython, so PyPy or any other Python implementation
    is not supported.
- OpenDDS
  - Right now this is being developed using the master branch of OpenDDS.
- CMake >= 3.12

## Building PyOpenDDS and Running the Basic Test

Assumptions:
- Unix environment with requirements met
  - When mature, PyOpenDDS should theoretically work on the intersection of all
    platforms that OpenDDS and CPython Support. Right now it's only being
    developed for Linux.
- `$DDS_ROOT/setenv.sh` has been sourced

```sh
bash build.sh
bash build_test.sh
bash test.sh
```
