- Alternative Simple API
- Instead of CPython C API, use C middle man libraries and use ctypes to call
  these. Allows for using other Python implementations that implement ctypes
  like PyPy.
- Implement annotations and constants in ITL, or alternatively read IDL file
  directly.
