# PyOpenDDS

Python Bindings for [OpenDDS](https://github.com/objectcomputing/OpenDDS).

**WARNING: This project is still a work in progress!**

**The vast majority of DDS functionality is not implemented yet and the major
question of type support/IDL maping has still not been answered.**

## Requirements

- Python >= 3.6
- OpenDDS
  - Currently using
    [iguessthislldo/igtd/python](https://github.com/iguessthislldo/OpenDDS/tree/igtd/python).
    For now this is just CMake Support in OpenDDS that hasn't been merged into
    master yet. Python support may or may not be added to opendds_idl in the same
    method that [Node-OpenDDS](https://github.com/oci-labs/node-opendds) uses.
- CMake

## Building PyOpenDDS and Running the Test

Assumptions:
- Unix environment with requirements met
  - When mature, PyOpenDDS should theoretically work on the intersection of all
    platoforms that OpenDDS and Python3 Support.
- `$DDS_ROOT/setenv.sh` has been sourced
- A Python virtualenv named `.venv` has been set up in the root of the repo.

```sh
bash build.sh
bash build_test.sh
bash test.sh
```

## TODO

- [ ] Basic `test.py` without interacting with Sample Data
- [ ] Python IDL Mapping
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
