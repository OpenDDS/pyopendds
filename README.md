# PyOpenDDS

Python Bindings for [OpenDDS](https://github.com/objectcomputing/OpenDDS).

## Requirements

- Python >= 3.6
- OpenDDS (Exact Requirements TBD)
- CMake

## Running Test

Assumptions:
- Unix environment with requirements met
- `$DDS_ROOT/setenv.sh` has been sourced
- A Python virtualenv named `.venv` has been set up in the root of the repo.

Run `bash build.sh` to build PyOpenDDS and the test and `bash test.sh` to run
the test application.

## TODO

- [ ] Basic `test.py` without interacting with Sample Data
- [ ] Python IDL Mapping
- [ ] Type Support for Python Mapping
- [ ] Interactions with sample data in `test.py`.
- [ ] Replace Shell Scripts with Python
- [ ] Integrate CMake with CPython Native Extension Build
- [ ] Integration with Python asyncio somehow
- [ ] Implementation Progress:
  - [ ] Participant (Started)
  - [ ] Subscriber (Started)
  - [ ] DataReader (Started)
  - [ ] Publisher 
  - [ ] DataWriter
  - [X] Wait Sets (as `DataReader.wait_for(status : StatusKind)`)
  - [ ] QOS
  - [ ] DataReader Listener
