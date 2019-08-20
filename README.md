# PyOpenDDS

Python Bindings for [OpenDDS](https://github.com/objectcomputing/OpenDDS).

**WARNING: This project is still a work in progress!**

## Requirements

- Python >= 3.7
  - This uses the C API of CPython, so PyPy, or any other Python implementation
    is not supported.
- OpenDDS
  - Currently using
    [iguessthislldo/igtd/python](https://github.com/iguessthislldo/OpenDDS/tree/igtd/python)
    As the test bed for adding Python support to OpenDDS.
- CMake

## Building PyOpenDDS and Running the Test

Assumptions:
- Unix environment with requirements met
  - When mature, PyOpenDDS should theoretically work on the intersection of all
    platforms that OpenDDS and CPython Support.
- `$DDS_ROOT/setenv.sh` has been sourced
- A Python virtualenv named `.venv` has been set up in the root of the repo.

```sh
bash build_test.sh
bash build.sh
bash test.sh
```

## TODO

- [ ] Basic `test.py` without interacting with Sample Data
- [ ] Python IDL Mapping (Started)
- [ ] Type Support for Python Mapping
- [ ] Interactions with sample data in `test.py`.
- [ ] Replace Shell Scripts with Python
- [X] Integrate CMake with CPython Native Extension Build
- [ ] Implementation Progress:
  - [ ] Participant (Started)
  - [ ] Subscriber (Started)
  - [ ] DataReader (Started)
  - [ ] Publisher 
  - [ ] DataWriter
  - [X] Wait Sets (as `DataReader.wait_for(status : StatusKind)`)
  - [ ] QOS
  - [ ] DataReader Listener
- [ ] Sphinx-based Documentation like a true Python Library
