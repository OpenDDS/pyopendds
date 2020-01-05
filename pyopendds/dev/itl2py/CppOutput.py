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

    for name in idl_names:
      self.append('#include <' + name + 'TypeSupportImpl.h>')
    self.append('''
#include <dds/DdsDcpsDomainC.h>

#include <Python.h>

#include <stdexcept>

namespace PyOpenDDS {

/// Get Contents of Capsule from a PyObject
template <typename T>
T* get_capsule(PyObject* obj)
{
  T* rv = 0;
  PyObject* capsule = PyObject_GetAttrString(obj, "_var");
  if (capsule && PyCapsule_CheckExact(capsule)) {
    rv = static_cast<T*>(PyCapsule_GetPointer(capsule, NULL));
  }
  return rv;
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

template<typename T>
class TypeBase {
public:
  typedef typename OpenDDS::DCPS::DDSTraits<T> Traits;
  typedef typename Traits::TypeSupportType TypeSupport;
  typedef typename Traits::TypeSupportTypeImpl TypeSupportImpl;

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

  static void register_type(PyObject* pyparticipant)
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
};
template<typename T> class Type;

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
class Type<''' + cpp_name + '''> : public TypeBase<''' + cpp_name + '''> {
public:

  static PyObject* get_python_class()
  {
    PyObject* module = PyImport_ImportModule("''' + self.python_package_name + '''");
    if (!module) return 0;''')

    for name in struct_type.parent_name().parts:
      self.append('''\
    module = PyObject_GetAttrString(module, "''' + name + '''");
    if (!module) return 0;''')

    self.append('''\
    return PyObject_GetAttrString(module, "''' + struct_type.local_name() + '''");
  }

  static void to_python(const ''' + cpp_name + '''& cpp, PyObject*& py)
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

  static ''' + cpp_name + ''' from_python(PyObject* py)
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
};
''')

  def visit_enum(self, enum_type):
    pass

  def after(self):
    def for_each_topic_type(what):
      lines = ''
      first = True
      for topic_type in self.topic_types:
        if first:
          lines += '  '
          first = False
        else:
          lines += ' else '
        lines += '''\
if (pytype == PyOpenDDS::Type<''' + topic_type + '''>::get_python_class()) {
''' + what(topic_type) + '''\
  }'''
      return lines
    lines = '''\
} // PyOpenDDS\n

static PyObject* pyregister_type(PyObject* self, PyObject* args)
{
  // Get Arguments
  PyObject* pyparticipant;
  PyObject* pytype;
  if (!PyArg_ParseTuple(args, "OO", &pyparticipant, &pytype)) {
    PyErr_SetString(PyExc_TypeError, "Invalid Arguments");
    return NULL;
  }

''' + for_each_topic_type(lambda topic_type: '''\
    PyOpenDDS::Type<''' + topic_type + '''>::register_type(pyparticipant);
    Py_RETURN_NONE;
''') + '''

  PyErr_SetString(PyExc_Exception, "Could Not Match Python Type");
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

  const char* type_name = 0;

''' + for_each_topic_type(lambda topic_type: '''\
    type_name = PyOpenDDS::Type<''' + topic_type + '''>::Traits::type_name();
''') + '''

  if (type_name) {
    return PyUnicode_FromString(type_name);
  }

  PyErr_SetString(PyExc_Exception, "Could Not Get OpenDDS Type Name");
  return NULL;
}

static PyMethodDef ''' + self.native_package_name + '''_Methods[] = {
  {
    "register_type", pyregister_type, METH_VARARGS, ""
  },
  {
    "type_name", pytype_name, METH_VARARGS, ""
  },
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
  return PyModule_Create(&''' + self.native_package_name + '''_Module);
}
'''
    return lines
