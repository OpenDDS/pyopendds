#include <Python.h>

static PyObject* print(PyObject* self, PyObject* args)
{
  const char* string;
  if (!PyArg_ParseTuple(args, "s", &string)) {
    return NULL;
  }
  printf("print<%s>\n", string);
  Py_RETURN_NONE;
}

static PyObject* Error;

static PyMethodDef pyopendds_Methods[] = {
  { "print", print, METH_VARARGS, "print something" },
  { NULL, NULL, 0, NULL }
};

static struct PyModuleDef pyopendds_Module = {
  PyModuleDef_HEAD_INIT,
  "_pyopendds", "Internal Python Bindings for OpenDDS",
  -1,
  pyopendds_Methods
};

PyMODINIT_FUNC PyInit__pyopendds()
{
  PyObject* module = PyModule_Create(&pyopendds_Module);
  if (module == NULL) {
    return NULL;
  }

  // _pyopendds.Error
  Error = PyErr_NewException("_pyopendds.Error", NULL, NULL);
  Py_INCREF(Error);
  PyModule_AddObject(module, "Error", Error);

  return module;
}
