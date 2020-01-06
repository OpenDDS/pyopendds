from pathlib import Path
from typing import List

from .ast import Output, PrimitiveType

class CppOutput(Output):

  def __init__(self, output_path: Path,
      python_package_name: str,
      native_package_name: str,
      idl_names: List[str]):
    self.python_package_name = python_package_name
    self.native_package_name = native_package_name
    super().__init__(output_path / (native_package_name + '.cpp'))

    self.topic_types = []

    self.append('#include <Python.h>\n\n')

    for name in idl_names:
      self.append('#include <' + name + 'TypeSupportImpl.h>')
    self.append('''
#include <dds/DdsDcpsDomainC.h>
#include <dds/DCPS/WaitSet.h>

#include <stdexcept>
#include <map>
#include <memory>

namespace {

/// Get Contents of Capsule from a PyObject
template <typename T>
T* get_capsule(PyObject* obj)
{
  T* rv = nullptr;
  PyObject* capsule = PyObject_GetAttrString(obj, "_var");
  if (capsule && PyCapsule_IsValid(capsule, nullptr)) {
    rv = static_cast<T*>(PyCapsule_GetPointer(capsule, nullptr));
  }
  return rv;
}

// Python Objects To Keep
PyObject* pyopendds;
PyObject* PyOpenDDS_Error;
PyObject* ReturnCodeError;

bool cache_python_objects()
{
  // Get pyopendds
  pyopendds = PyImport_ImportModule("pyopendds");
  if (!pyopendds) return true;

  // Get PyOpenDDS_Error
  PyOpenDDS_Error = PyObject_GetAttrString(pyopendds, "PyOpenDDS_Error");
  if (!PyOpenDDS_Error) return true;
  Py_INCREF(PyOpenDDS_Error);

  // Get ReturnCodeError
  ReturnCodeError = PyObject_GetAttrString(pyopendds, "ReturnCodeError");
  if (!ReturnCodeError) return true;
  Py_INCREF(ReturnCodeError);

  return false;
}

bool check_rc(DDS::ReturnCode_t rc)
{
  return !PyObject_CallMethod(ReturnCodeError, "check", "k", rc);
}

class Exception : public std::exception {
public:
  Exception(const char* message)
  : message_(message)
  {
  }

  virtual const char* what() const noexcept
  {
    return message_;
  }

private:
  const char* message_;
};

class TypeBase {
public:
  virtual void register_type(PyObject* pyparticipant) = 0;
  virtual PyObject* get_python_class() = 0;
  virtual const char* type_name() = 0;
  virtual PyObject* read(PyObject* pyreader) = 0;
};

template<typename T>
class TemplatedTypeBase : public TypeBase {
public:
  typedef typename OpenDDS::DCPS::DDSTraits<T> Traits;

  typedef T IdlType;
  typedef typename Traits::MessageSequenceType IdlTypeSequence;

  typedef typename Traits::TypeSupportType TypeSupport;
  typedef typename Traits::TypeSupportTypeImpl TypeSupportImpl;
  typedef typename Traits::DataWriterType DataWriter;
  typedef typename Traits::DataReaderType DataReader;

  const char* type_name()
  {
    return Traits::type_name();
  }

  /**
   * Callback for Python to call when the TypeSupport capsule is deleted
   */
  static void delete_typesupport(PyObject* capsule)
  {
    if (PyCapsule_CheckExact(capsule)) {
      delete static_cast<TypeSupportImpl*>(
        PyCapsule_GetPointer(capsule, NULL));
    }
  }

  void register_type(PyObject* pyparticipant)
  {
    // Get DomainParticipant_var
    DDS::DomainParticipant* participant =
      get_capsule<DDS::DomainParticipant>(pyparticipant);
    if (!participant) {
      throw Exception("Could not get native particpant");
    }

    // Register with OpenDDS
    TypeSupportImpl* type_support = new TypeSupportImpl;
    if (type_support->register_type(participant, "") != DDS::RETCODE_OK) {
      delete type_support;
      type_support = 0;
      throw Exception("Could not create register type");
    }

    // Store TypeSupport in Python Participant
    PyObject* capsule = PyCapsule_New(participant, NULL, delete_typesupport);
    if (!capsule) {
      throw Exception("Could not create ts capsule");
    }
    PyObject* list = PyObject_GetAttrString(
      pyparticipant, "_registered_typesupport");
    if (!list || !PyList_Check(list)) {
      throw Exception("Could not get ts list");
    }
    if (PyList_Append(list, capsule)) {
      PyErr_Print();
      throw Exception("Could not append ts to list");
    }
  }

  virtual void to_python(const T& cpp, PyObject*& py) = 0;

  PyObject* read(PyObject* pyreader)
  {
    DDS::DataReader* reader = get_capsule<DDS::DataReader>(pyreader);
    if (!reader) {
      PyErr_SetString(PyOpenDDS_Error, "Could not get datareader");
      return nullptr;
    }

    DataReader* reader_impl = DataReader::_narrow(reader);
    if (!reader_impl) {
      PyErr_SetString(PyOpenDDS_Error, "Could not narrow reader implementation");
      return nullptr;
    }

    DDS::ReturnCode_t rc;
    DDS::ReadCondition_var read_condition = reader_impl->create_readcondition(
      DDS::ANY_SAMPLE_STATE, DDS::ANY_VIEW_STATE, DDS::ANY_SAMPLE_STATE);
    DDS::WaitSet_var ws = new DDS::WaitSet;
    ws->attach_condition(read_condition);
    DDS::ConditionSeq active;
    const DDS::Duration_t max_wait_time = {10, 0};
    rc = ws->wait(active, max_wait_time);
    ws->detach_condition(read_condition);
    reader_impl->delete_readcondition(read_condition);

    T sample;
    DDS::SampleInfo info;
    if (check_rc(reader_impl->take_next_sample(sample, info))) return nullptr;
    PyObject *rv = nullptr;
    to_python(sample, rv);
    return rv;
  }

  virtual T from_python(PyObject* py) = 0;
};
template<typename T> class Type;

typedef std::shared_ptr<TypeBase> TypePtr;
typedef std::map<PyObject*, TypePtr> Types;
Types types;

template<typename T>
void init_type()
{
  TypePtr type{new Type<T>};
  types.insert(Types::value_type(type->get_python_class(), type));
}

long get_python_long_attr(PyObject* py, const char* attr_name)
{
  PyObject* attr = PyObject_GetAttrString(py, attr_name);
  if (!attr) {
    PyErr_Print();
    throw Exception("python error occured");
  }
  if (!PyLong_Check(attr)) {
    throw Exception("python attribute isn't an int");
  }
  long long_value = PyLong_AsLong(attr);
  if (long_value == -1 && PyErr_Occurred()) {
    PyErr_Print();
    throw Exception("python error occured");
  }
  return long_value;
}
''')

  def visit_struct(self, struct_type):
    cpp_name = '::' + struct_type.name.join('::')
    if struct_type.is_topic_type:
      self.topic_types.append(cpp_name)
    self.append('''\
template<>
class Type<''' + cpp_name + '''> : public TemplatedTypeBase<''' + cpp_name + '''> {
public:
  PyObject* get_python_class()
  {
    if (!python_class_) {
      PyObject* module = PyImport_ImportModule("''' + self.python_package_name + '''");
      if (!module) return 0;''')

    for name in struct_type.parent_name().parts:
      self.append('''\
      module = PyObject_GetAttrString(module, "''' + name + '''");
      if (!module) return 0;''')

    self.append('''\
      python_class_ = PyObject_GetAttrString(module, "''' + struct_type.local_name() + '''");
    }
    return python_class_;
  }

  void to_python(const ''' + cpp_name + '''& cpp, PyObject*& py)
  {
    PyObject* cls = get_python_class();
    if (py) {
      if (PyObject_IsInstance(cls, py) != 1) {
        throw Exception("Python object is not a valid type");
      }
    } else {
      py = PyObject_CallObject(cls, nullptr);
      if (!py) {
        PyErr_Print();
        throw Exception("Could not call __init__ for new class");
      }
    }
''');

    for field_name, (field_type, _) in struct_type.fields.items():
      if isinstance(field_type, PrimitiveType) and field_type.is_int():
        self.append('''\
    if (PyObject_SetAttrString(py, "''' + field_name + '''", PyLong_FromLong(cpp.''' + field_name + '''))) {
      PyErr_Print();
      throw Exception("Type<''' + cpp_name + '''>::to_python: Could not set ''' + field_name + '''");
    }''')
      else:
        self.append('    // ' + field_name + ' was left unimplemented')

    self.append('''\
  }

  ''' + cpp_name + ''' from_python(PyObject* py)
  {
    ''' + cpp_name + ''' rv;

    PyObject* cls = get_python_class();
    if (PyObject_IsInstance(py, cls) != 1) {
      throw Exception("Python object is not a valid type");
    }
''');

    for field_name, (field_type, _) in struct_type.fields.items():
      if isinstance(field_type, PrimitiveType) and field_type.is_int():
        self.append('''\
    rv.''' + field_name + ''' = get_python_long_attr(py, "''' + field_name + '''");''')
      else:
        self.append('    // ' + field_name + ' was left unimplemented')

    self.append('''
    return rv;
  }

private:
  PyObject* python_class_ = nullptr;
};
''')

  def visit_enum(self, enum_type):
    pass

  def after(self):
    lines = '''\
} // Anonymous Namespace\n

static PyObject* pyregister_type(PyObject* self, PyObject* args)
{
  // Get Arguments
  PyObject* pyparticipant;
  PyObject* pytype;
  if (!PyArg_ParseTuple(args, "OO", &pyparticipant, &pytype)) {
    PyErr_SetString(PyExc_TypeError, "Invalid Arguments");
    return NULL;
  }

  Types::iterator i = types.find(pytype);
  if (i != types.end()) {
    i->second->register_type(pyparticipant);
    Py_RETURN_NONE;
  }

  PyErr_SetString(PyExc_TypeError, "Invalid Type");
  return NULL;
}

static PyObject* pytype_name(PyObject* self, PyObject* args)
{
  // Get Arguments
  PyObject* pytype;
  if (!PyArg_ParseTuple(args, "O", &pytype)) {
    PyErr_SetString(PyExc_TypeError, "Invalid Arguments");
    return NULL;
  }

  Types::iterator i = types.find(pytype);
  if (i != types.end()) {
    return PyUnicode_FromString(i->second->type_name());
  }

  PyErr_SetString(PyExc_TypeError, "Invalid Type");
  return nullptr;
}

static PyObject* pyread(PyObject* self, PyObject* args)
{
  // Get Arguments
  PyObject* pyreader;
  if (!PyArg_ParseTuple(args, "O", &pyreader)) return nullptr;

  // Try to Get Topic Type and Do Read
  PyObject* pytopic = PyObject_GetAttrString(pyreader, "topic");
  if (!pytopic) return nullptr;
  PyObject* pytype = PyObject_GetAttrString(pytopic, "type");
  if (!pytype) return nullptr;
  Types::iterator i = types.find(pytype);
  if (i != types.end()) {
    return i->second->read(pyreader);
  }

  PyErr_SetString(PyExc_TypeError, "Invalid Type");
  return NULL;
}

static PyMethodDef ''' + self.native_package_name + '''_Methods[] = {
  {"register_type", pyregister_type, METH_VARARGS, ""},
  {"type_name", pytype_name, METH_VARARGS, ""},
  {"read", pyread, METH_VARARGS, ""},
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef ''' + self.native_package_name + '''_Module = {
  PyModuleDef_HEAD_INIT,
  "''' + self.native_package_name + '''", "",
  -1, // Global State Module, because OpenDDS uses Singletons
  ''' + self.native_package_name + '''_Methods
};

PyMODINIT_FUNC PyInit_''' + self.native_package_name + '''()
{
  PyObject* module = PyModule_Create(&''' + self.native_package_name + '''_Module);
  if (!module || cache_python_objects()) return nullptr;

'''
    for topic_type in self.topic_types:
      lines += '  init_type<' + topic_type + '>();\n'

    lines += '''\

  return module;
}
'''
    return lines
