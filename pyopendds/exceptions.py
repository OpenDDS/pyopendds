from .constants import ReturnCode

class PyOpenDDS_Error(Exception):
  '''Base for all errors in PyOpenDDS
  '''

class CppException(PyOpenDDS_Error):
  '''Raised when a C++ exception was thrown in the native code.
  '''

  def __init__(self, what):
    self.what = what

  def __str__(self):
    return 'Caught C++ Exception: ' + self.what

class ReturnCodeError(PyOpenDDS_Error):
  '''Raised when a ReturnCode_t other than RETURNCODE_OK was returned from a
  OpenDDS function that returns ReturnCode_t.

  There are subclasses for each ReturnCode, for example
  ImmutablePolicyReturnCodeError for ReturnCode.IMMUTABLE_POLICY.
  '''

  return_code = None
  dds_name = None
  subclasses = {}

  def __init__(self, unknown_code: int = None):
    self.unknown_code = unknown_code

  @classmethod
  def generate_subclasses(cls) -> None:
    for name, value in ReturnCode.__members__.items():
      if name != 'OK':
        dds_name = 'DDS::RETCODE_' + name
        name = name.title().replace('_', '') + 'ReturnCodeError'
        cls = type(name, (cls,), {'return_code': value, 'dds_name': dds_name})
        globals()[name] = cls
        cls.subclasses[value] = cls

  @classmethod
  def check(cls, rc : ReturnCode) -> None:
    try:
      rc = ReturnCode(rc)
    except ValueError:
      raise ReturnCodeError(rc)
    if rc != ReturnCode.OK and rc in ReturnCode:
      raise cls.subclasses[rc]

  def __str__(self):
    if self.return_code:
      return 'OpenDDS has returned ' + self.dds_name
    return 'OpenDDS has returned an ReturnCode_t unkown to PyOpenDDS: ' + \
      self.unknown_code

ReturnCodeError.generate_subclasses()

class CreateEntityError(PyOpenDDS_Error):
  '''Raised when a function for creating a DDS Entity returned nullptr.
  '''

  def __init__(self, what):
    self.what = what

  def __str__(self):
    return 'Error while creating ' + self.what
