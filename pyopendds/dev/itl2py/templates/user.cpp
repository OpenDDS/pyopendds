#include <pyopendds/user.hpp> // Must always be first include
/*{% for name in idl_names %}*/
#include </*{{ name }}*/TypeSupportImpl.h>
/*{%- endfor %}*/

namespace pyopendds {

PyObject* Errors::pyopendds_ = nullptr;
PyObject* Errors::PyOpenDDS_Error_ = nullptr;
PyObject* Errors::ReturnCodeError_ = nullptr;

TopicTypeBase::TopicTypes TopicTypeBase::topic_types_;

/*{%- for type in types %}*/

template<>
class Type</*{{ type.cpp_name }}*/> {
public:
  static PyObject* get_python_class()
  {
    static PyObject* python_class = nullptr;
    if (!python_class) {
      Ref module = PyImport_ImportModule("/*{{ package_name }}*/");
      if (!module) throw Exception();

      /*{% for name in type.name_parts -%}*/
      module = PyObject_GetAttrString(*module, "/*{{ name }}*/");
      if (!module) throw Exception();
      /*{%- endfor %}*/

      python_class = PyObject_GetAttrString(*module, "/*{{ type.local_name }}*/");
      if (!python_class) throw Exception();
    }
    return python_class;
  }

  static void cpp_to_python(const /*{{ type.cpp_name }}*/& cpp, PyObject*& py)
  {
    PyObject* const cls = get_python_class();
    /*{% if type.to_replace %}*/
    if (py) Py_DECREF(py);
    PyObject* args;
    /*{{ type.new_lines | indent(4) }}*/
    py = PyObject_CallObject(cls, args);
    /*{% else %}*/
    if (py) {
      if (PyObject_IsInstance(cls, py) != 1) {
        throw Exception("Not a /*{{ type.py_name }}*/", PyExc_TypeError);
      }
    } else {
      PyObject* args;
      /*{{ type.new_lines | indent(6) }}*/
      py = PyObject_CallObject(cls, args);
    }
    /*{% if type.to_lines %}*//*{{ type.to_lines | indent(4) }}*//*{% endif %}*/
    /*{% endif %}*/
  }

  static void python_to_cpp(PyObject* py, /*{{ type.cpp_name }}*/& cpp)
  {
    PyObject* const cls = get_python_class();
    /*{{ type.from_lines | indent(4) }}*/
  }
};

/*{%- endfor %}*/

} // namespace pyopendds

namespace {

using namespace pyopendds;

PyObject* pyregister_type(PyObject* self, PyObject* args)
{
  Ref pyparticipant;
  Ref pytype;
  if (!PyArg_ParseTuple(args, "OO", &*pyparticipant, &*pytype)) return nullptr;
  pyparticipant++;
  pytype++;

  try {
    TopicTypeBase::find(*pytype)->register_type(*pyparticipant);
    Py_RETURN_NONE;
  } catch (const Exception& e) {
    return e.set();
  }
}

PyObject* pytype_name(PyObject* self, PyObject* args)
{
  Ref pytype;
  if (!PyArg_ParseTuple(args, "O", &*pytype)) return nullptr;
  pytype++;

  try {
    return PyUnicode_FromString(TopicTypeBase::find(*pytype)->type_name());
  } catch (const Exception& e) {
    return e.set();
  }
}

PyObject* pytake_next_sample(PyObject* self, PyObject* args)
{
  Ref pyreader;
  if (!PyArg_ParseTuple(args, "O", &*pyreader)) return nullptr;
  pyreader++;

  // Try to Get Topic Type and Do Read
  Ref pytopic = PyObject_GetAttrString(*pyreader, "topic");
  if (!pytopic) return nullptr;
  Ref pytype = PyObject_GetAttrString(*pytopic, "type");
  if (!pytype) return nullptr;

  try {
    return TopicTypeBase::find(*pytype)->take_next_sample(*pyreader);
  } catch (const Exception& e) {
    return e.set();
  }
}

PyMethodDef /*{{ native_package_name }}*/_Methods[] = {
  {"register_type", pyregister_type, METH_VARARGS, ""},
  {"type_name", pytype_name, METH_VARARGS, ""},
  {"take_next_sample", pytake_next_sample, METH_VARARGS, ""},
  {nullptr, nullptr, 0, nullptr}
};

PyModuleDef /*{{ native_package_name }}*/_Module = {
  PyModuleDef_HEAD_INIT,
  "/*{{ native_package_name }}*/", "",
  -1, // Global State Module, because OpenDDS uses Singletons
  /*{{ native_package_name }}*/_Methods
};

} // namespace

PyMODINIT_FUNC PyInit_/*{{ native_package_name }}*/()
{
  PyObject* module = PyModule_Create(&/*{{ native_package_name }}*/_Module);
  if (!module || pyopendds::Errors::cache()) return nullptr;
  /*{% for type in types %}*//*{% if type.is_topic_type %}*/
  TopicType</*{{ type.cpp_name }}*/>::init();
  /*{%- endif %}*//*{% endfor %}*/

  return module;
}
