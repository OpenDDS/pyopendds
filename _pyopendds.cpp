#include <Python.h>

#include <string>
#include <vector>

#include <dds/DdsDcpsInfrastructureC.h>
#include <dds/DCPS/Service_Participant.h>

#include "MessengerTypeSupportImpl.h"

// Global Participant Factory
DDS::DomainParticipantFactory_var participant_factory;

// _pyopendds.Error
static PyObject* Error;

// init_opendds(*args[str]) -> None
static PyObject* init_opendds(PyObject* self, PyObject* args)
{
  /*
   * In addition to the need to convert the arguments into an argv array,
   * OpenDDS will mess with argv and argc so we need to create copies that we
   * can cleanup properly afterwords.
   */
  int original_argc = PySequence_Size(args);
  int argc = original_argc;
  char** original_argv = new char*[argc];
  char** argv = new char*[argc];
  if (!original_argv || !argv) {
    PyErr_SetString(Error, "Allocation Failed");
    return NULL;
  }
  for (int i = 0; i < argc; i++) {
    PyObject* obj = PySequence_GetItem(args, i);
    if (!obj) {
      PyErr_SetString(Error, "Failed to get argument");
      return NULL;
    }
    Py_INCREF(obj);
    PyObject* string_obj = PyObject_Str(obj);
    if (!string_obj) {
      PyErr_SetString(Error, "Failed to create string from argument");
      return NULL;
    }
    Py_INCREF(string_obj);
    char* string;
    ssize_t string_len;
    string = PyUnicode_AsUTF8AndSize(string_obj, &string_len);
    if (!string) {
      PyErr_SetString(Error, "Failed to create UTF-8 C string from argument");
      return NULL;
    }
    char* duplicate = new char[string_len];
    if (!duplicate) {
      PyErr_SetString(Error, "Allocation Failed");
      return NULL;
    }
    argv[i] = original_argv[i] = strncpy(duplicate, string, string_len);
    Py_DECREF(string_obj);
    Py_DECREF(obj);
  }

  // Initialize OpenDDS
  participant_factory = TheParticipantFactoryWithArgs(argc, argv);
  if (CORBA::is_nil(participant_factory.in())) {
    PyErr_SetString(Error, "Failed to get ParticipantFactory");
    return NULL;
  }

  // Cleanup args
  for (int i = 0; i < original_argc; i++) {
    delete original_argv[i];
  }
  delete [] original_argv;
  delete [] argv;

  // return None
  Py_RETURN_NONE;
}

static PyMethodDef pyopendds_Methods[] = {
  {
    "init_opendds", init_opendds, METH_VARARGS,
    "Initialize OpenDDS, using DDS::TheParticipantFactoryWithArgs"
  },
  { NULL, NULL, 0, NULL }
};

static struct PyModuleDef pyopendds_Module = {
  PyModuleDef_HEAD_INIT,
  "_pyopendds", "Internal Python Bindings for OpenDDS",
  -1, // Global State Module, because OpenDDS uses Singletons
  pyopendds_Methods
};

PyMODINIT_FUNC PyInit__pyopendds()
{
  // Create _pyopendds
  PyObject* module = PyModule_Create(&pyopendds_Module);
  if (module == NULL) {
    return NULL;
  }

  // Add _pyopendds.Error
  Error = PyErr_NewException("_pyopendds.Error", NULL, NULL);
  Py_INCREF(Error);
  PyModule_AddObject(module, "Error", Error);

  return module;
}
