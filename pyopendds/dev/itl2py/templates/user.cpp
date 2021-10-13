#include <pyopendds/user.hpp> // Must always be first include
/*{% for name in idl_names %}*/
#include </*{{ name }}*/TypeSupportImpl.h>
/*{%- endfor %}*/
#include <iostream>
#include <sstream>

namespace pyopendds {

PyObject* Errors::pyopendds_ = nullptr;
PyObject* Errors::PyOpenDDS_Error_ = nullptr;
PyObject* Errors::ReturnCodeError_ = nullptr;

//TopicTypeBase::TopicTypes TopicTypeBase::topic_types_;

/*{%- for type in types %}*/

template<>
class Type</*{{ type.cpp_name }}*/> {
public:
  static PyObject* get_python_class()
  {
    PyObject* python_class = nullptr;
    if (!python_class) {
      std::stringstream mod_ss;
      mod_ss << "/*{{ package_name }}*/";
      /*{% for name in type.name_parts -%}*/
      mod_ss << "./*{{name}}*/";
      /*{% endfor -%}*/
      Ref module = PyImport_ImportModule(mod_ss.str().c_str());

      if (!module) {
        std::stringstream msg;
        msg << "Could not import module ";
        msg << mod_ss.str();
        throw Exception(msg.str().c_str(), PyExc_ImportError);
      }

      python_class = PyObject_GetAttrString(*module, "/*{{ type.local_name }}*/");
      if (!python_class) {
        std::stringstream msg;
        msg << "/*{{ type.local_name }}*/ ";
        msg << "does not exist in ";
        msg << mod_ss.str();
        throw Exception(msg.str().c_str(), PyExc_ImportError);
      }
    }
    return python_class;
  }

  static void cpp_to_python(const /*{{ type.cpp_name }}*/& cpp, PyObject*& py)
  {
    PyObject* cls = get_python_class();
    /*{%- if type.to_replace %}*/
    if (py) Py_DECREF(py);
    PyObject* args;
    /*{{ type.new_lines | indent(4) }}*/
    py = PyObject_CallObject(cls, args);
    /*{% else %}*/
    /*{% if type.sequence %}*/
    if (py) Py_DECREF(py);
    py = nullptr;
    /*{% endif %}*/
    PyObject* args;
    /*{{ type.new_lines | indent(6) }}*/
    py = PyObject_CallObject(cls, args);
    /*{% if type.to_lines %}*//*{{ type.to_lines | indent(4) }}*//*{% endif %}*/
    /*{%- endif %}*/
  }

  static void python_to_cpp(PyObject* py, /*{{ type.cpp_name }}*/& cpp)
  {
    PyObject* cls = get_python_class();
    /*{% if type.to_replace %}*/
    cpp = static_cast</*{{ type.cpp_name }}*/>(PyLong_AsLong(py));
    /*{% else %}*/
    if (py) {
      if (PyObject_IsInstance(py, cls) != 1 && PyObject_IsSubclass(cls, PyObject_Type(py)) != 1) {
        const char * actual_type = PyUnicode_AsUTF8(PyObject_GetAttrString(PyObject_Type(py),"__name__"));
        std::stringstream msg;
        msg << "python_to_cpp: PyObject(";
        msg << actual_type;
        msg << ") is not of type";
        msg << "/*{{ type.local_name }}*/ nor is not parent class.";
        throw Exception(msg.str().c_str(), PyExc_TypeError);
      }
    } else {
      PyObject* args;
      /*{{ type.new_lines | indent(6) }}*/
      py = PyObject_CallObject(cls, args);
    }
    /*{% if type.from_lines %}*//*{{ type.from_lines | indent(4) }}*//*{% endif %}*/
    /*{% endif %}*/
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

PyObject* pywrite(PyObject* self, PyObject* args)
{
  Ref pywriter;
  Ref pysample;
  if (!PyArg_ParseTuple(args, "OO", &*pywriter, &*pysample)) return nullptr;
  pywriter++;
  pysample++;
  
  // Try to Get Reading Type and Do write
  Ref pytopic = PyObject_GetAttrString(*pywriter, "topic");
  if (!pytopic) return nullptr;
  Ref pytype = PyObject_GetAttrString(*pytopic, "type");
  if (!pytype) return nullptr;

  try {
    return TopicTypeBase::find(*pytype)->write(*pywriter, *pysample);
  } catch (const Exception& e) {
    return e.set();
  }
}

PyMethodDef /*{{ native_package_name }}*/_Methods[] = {
  {"register_type", pyregister_type, METH_VARARGS, ""},
  {"type_name", pytype_name, METH_VARARGS, ""},
  {"write", pywrite, METH_VARARGS, ""},
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
