from .constants import ReturnCode

class PyOpenDDS_Error(Exception):
  pass

class ReturnCodeError(PyOpenDDS_Error):
  return_code = None
  mapping = {}

  @classmethod
  def get_error(cls, rc: ReturnCode):
    return mapping[rc]

for name, value in ReturnCode.__members__.items():
  if name != 'OK':
    name = name.title().replace('_', '') + 'ReturnCodeError'
    globals()[name] = type(name, (ReturnCodeError,), {'return_code': value})
