# PyOpenDDS Design Notes

## Goals for Version 1.0

- Implment a Python version of the DDS API
- Implement annotations and constants in ITL (Requires changes to `opendds_idl`
  in OpenDDS), or alternatively read IDL file directly.

## Ideas

- Alternative Simple API.
  - Would try to reduce API to a `Reader` and a `Writer`.
- Instead of CPython C API, use C middle man libraries and use ctypes to call
  these. Allows for using other Python implementations that implement ctypes
  like PyPy.
- If OpenDDS supported XTypes dynamic data, use user written classes with
  proper annotations to define types.
