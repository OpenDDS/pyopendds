# PyOpenDDS

Proof of concept Python Bindings for OpenDDS.

## Usage (Current Test Script)

Assumptions:
- Unix environment
- `$DDS_ROOT/setenv.sh` has been sourced
- A virtualenv is set up like: `virtualenv -p /usr/bin/python3 .venv`

Run `bash build.sh` to build PyOpenDDS adn the test and `bash test.sh` to run
the test application.

## TODO

- [ ] Basic `test.py` without interacting with Sample Data
- [ ] Python IDL Mapping
- [ ] Type Support for Python Mapping
- [ ] Interactions with sample data in `test.py`.
