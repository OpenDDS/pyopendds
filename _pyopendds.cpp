#include <Python.h>

#include <string>
#include <vector>

#include <dds/DdsDcpsInfrastructureC.h>
#include <dds/DCPS/Service_Participant.h>

#include "MessengerTypeSupportImpl.h"

// Global Participant Factory
DDS::DomainParticipantFactory_var participant_factory;

// _pyopendds.Error
static PyObject* PyOpenDDS_Error;

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
    PyErr_SetString(PyOpenDDS_Error, "Allocation Failed");
    return NULL;
  }
  for (int i = 0; i < argc; i++) {
    PyObject* obj = PySequence_GetItem(args, i);
    if (!obj) {
      PyErr_SetString(PyOpenDDS_Error, "Failed to get argument");
      return NULL;
    }
    Py_INCREF(obj);
    PyObject* string_obj = PyObject_Str(obj);
    if (!string_obj) {
      PyErr_SetString(PyOpenDDS_Error, "Failed to create string from argument");
      return NULL;
    }
    Py_INCREF(string_obj);
    char* string;
    ssize_t string_len;
    string = PyUnicode_AsUTF8AndSize(string_obj, &string_len);
    if (!string) {
      PyErr_SetString(PyOpenDDS_Error, "Failed to create UTF-8 C string from argument");
      return NULL;
    }
    char* duplicate = new char[string_len];
    if (!duplicate) {
      PyErr_SetString(PyOpenDDS_Error, "Allocation Failed");
      return NULL;
    }
    argv[i] = original_argv[i] = strncpy(duplicate, string, string_len);
    Py_DECREF(string_obj);
    Py_DECREF(obj);
  }

  // Initialize OpenDDS
  participant_factory = TheParticipantFactoryWithArgs(argc, argv);
  if (CORBA::is_nil(participant_factory.in())) {
    PyErr_SetString(PyOpenDDS_Error, "Failed to get ParticipantFactory");
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

void delete_participant_var(PyObject* var) {
  if (PyCapsule_CheckExact(var)) {
    DDS::DomainParticipant_var participant = static_cast<DDS::DomainParticipant*>(
      PyCapsule_GetPointer(var, NULL));
    participant = 0;
  }
}

/*
 * create_participant(participant: DomainParticipant, domain: int) -> None
 */
static PyObject* create_participant(PyObject* self, PyObject* args)
{
  PyObject* participant_obj = PySequence_GetItem(args, 0);
  // TODO: Check this is a DomainParticipant
  if (!participant_obj) {
    PyErr_SetString(PyOpenDDS_Error, "No Participant Given");
    return NULL;
  }

  PyObject* domain_obj = PySequence_GetItem(args, 1);
  if (!domain_obj) {
    PyErr_SetString(PyOpenDDS_Error, "Domain argument is NULL");
    return NULL;
  }
  PyObject* domain_long_obj = PyNumber_Long(domain_obj);
  if (!domain_long_obj) {
    PyErr_SetString(PyOpenDDS_Error, "Invalid Domain argument");
    return NULL;
  }
  long domain = PyLong_AsLong(domain_obj);

  DDS::DomainParticipantQos qos;
  participant_factory->get_default_participant_qos(qos);
  DDS::DomainParticipant_var participant =
    participant_factory->create_participant(
      domain, qos,
      DDS::DomainParticipantListener::_nil(),
      OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (CORBA::is_nil(participant.in())) {
    PyErr_SetString(PyOpenDDS_Error, "Failed to get Participant");
    return NULL;
  }

  PyObject* var = PyCapsule_New(
    participant._retn(), NULL, delete_participant_var);
  if (!var) {
    PyErr_SetString(PyOpenDDS_Error, "Failed Wrap Participant");
    return NULL;
  }

  PyObject_SetAttrString(participant_obj, "_var", var);

  Py_RETURN_NONE;
}

static PyObject* create_subscriber(PyObject* self, PyObject* args)
{
}

static PyObject* create_topic(PyObject* self, PyObject* args)
{
}

static PyObject* create_datareader(PyObject* self, PyObject* args)
{
}

static PyMethodDef pyopendds_Methods[] = {
  {
    "init_opendds", init_opendds, METH_VARARGS,
    "Initialize OpenDDS, using DDS::TheParticipantFactoryWithArgs"
  },
  { "create_participant", create_participant, METH_VARARGS, "" },
  { "create_subscriber", create_subscriber, METH_VARARGS, "" },
  { "create_topic", create_topic, METH_VARARGS, "" },
  { "create_datareader", create_datareader, METH_VARARGS, "" },
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
  PyOpenDDS_Error = PyErr_NewException("_pyopendds.PyOpenDDS_Error", NULL, NULL);
  Py_INCREF(PyOpenDDS_Error);
  PyModule_AddObject(module, "PyOpenDDS_Error", PyOpenDDS_Error);

  return module;
}
