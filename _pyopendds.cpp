#include <Python.h>

#include <string>
#include <vector>

#include <dds/DdsDcpsInfrastructureC.h>
#include <dds/DCPS/Service_Participant.h>
#include <dds/DCPS/Marked_Default_Qos.h>

// HARDCODED
#include "ReadingTypeSupportImpl.h"

/// Name of PyCapule Attribute Holding the C++ Object
const char * VAR_NAME = "_var";

/// Global Participant Factory
DDS::DomainParticipantFactory_var participant_factory;

/// _pyopendds.Error
static PyObject* PyOpenDDS_Error;

/**
 * init_opendds(*args[str]) -> None
 */
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
    char* duplicate = new char[string_len + 1];
    duplicate[string_len] = '\0';
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

/**
 * Callback for Python to Call when the Python Participant is Deleted
 */
void delete_participant_var(PyObject* part_capsule)
{
  if (PyCapsule_CheckExact(part_capsule)) {
    DDS::DomainParticipant_var participant = static_cast<DDS::DomainParticipant*>(
      PyCapsule_GetPointer(part_capsule, NULL));
    participant = 0;
  }
}

/**
 * create_participant(participant: DomainParticipant, domain: int) -> None
 */
static PyObject* create_participant(PyObject* self, PyObject* args)
{
  // Get Arguments
  PyObject* pyparticipant = PySequence_GetItem(args, 0);
  if (!pyparticipant) {
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

  // Create Participant
  DDS::DomainParticipantQos qos;
  participant_factory->get_default_participant_qos(qos);
  DDS::DomainParticipant* participant =
    participant_factory->create_participant(
      domain, qos,
      DDS::DomainParticipantListener::_nil(),
      OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (!participant) {
    PyErr_SetString(PyOpenDDS_Error, "Failed to get Participant");
    return NULL;
  }

  // Attach OpenDDS Participant to Participant Python Object
  PyObject* var = PyCapsule_New(
    participant, NULL, delete_participant_var);
  if (!var || PyObject_SetAttrString(pyparticipant, VAR_NAME, var)) {
    PyErr_SetString(PyOpenDDS_Error, "Failed Wrap Participant");
    return NULL;
  }

  // return None
  Py_RETURN_NONE;
}

static PyObject* participant_cleanup(PyObject* self, PyObject* args)
{
  // Get Arguments
  PyObject* pyparticipant;
  if (!PyArg_ParseTuple(args, "O", &pyparticipant)) {
    PyErr_SetString(PyOpenDDS_Error, "Argument Parsing Failed");
    return NULL;
  }

  // Get DomainParticipant_var
  DDS::DomainParticipant* participant;
  PyObject* part_capsule = PyObject_GetAttrString(pyparticipant, VAR_NAME);
  bool valid_participant = part_capsule && PyCapsule_CheckExact(part_capsule);
  if (valid_participant) {
    participant = static_cast<DDS::DomainParticipant*>(
      PyCapsule_GetPointer(part_capsule, NULL));
  } else {
    PyErr_SetString(PyOpenDDS_Error,
      "Invalid Participant, Python Participant is Missing a Valid C++ Participant");
    return NULL;
  }

  // Cleanup
  participant->delete_contained_entities();

  // return None
  Py_RETURN_NONE;
}

/**
 * Callback for Python to Call when the Topic Capsule is Deleted
 */
void delete_topic_var(PyObject* topic_capsule)
{
  if (PyCapsule_CheckExact(topic_capsule)) {
    DDS::Topic_var topic = static_cast<DDS::Topic*>(
      PyCapsule_GetPointer(topic_capsule, NULL));
    topic = 0;
  }
}

/**
 * create_topic(topic: Topic, participant: DomainParticipant, topic_name: str, topic_type: str) -> None
 */
static PyObject* create_topic(PyObject* self, PyObject* args)
{
  // Get Arguments
  PyObject* pytopic;
  PyObject* pyparticipant;
  char* name;
  char* type;
  if (!PyArg_ParseTuple(args, "OOss", &pytopic, &pyparticipant, &name, &type)) {
    PyErr_SetString(PyOpenDDS_Error, "Argument Parsing Failed");
    return NULL;
  }

  // Get DomainParticipant
  DDS::DomainParticipant* participant;
  PyObject* part_capsule = PyObject_GetAttrString(pyparticipant, VAR_NAME);
  bool valid_participant = part_capsule && PyCapsule_CheckExact(part_capsule);
  if (valid_participant) {
    participant = static_cast<DDS::DomainParticipant*>(
      PyCapsule_GetPointer(part_capsule, NULL));
  } else {
    PyErr_SetString(PyOpenDDS_Error,
      "Invalid Participant, Python Participant is Missing a Valid C++ Participant");
    return NULL;
  }

  // HARDCODED Register Type
  Test::ReadingTypeSupport_var type_support = new
    Test::ReadingTypeSupportImpl();
  if (type_support->register_type(participant, "") != DDS::RETCODE_OK) {
    PyErr_SetString(PyOpenDDS_Error, "Failed to Register Type");
    return NULL;
  }

  // Create Topic
  DDS::Topic* topic = participant->create_topic(
    name, type, TOPIC_QOS_DEFAULT, 0,
    OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (!topic) {
    PyErr_SetString(PyOpenDDS_Error, "Create Topic Failed");
    return NULL;
  }

  // Attach OpenDDS Topic to Topic Python Object
  PyObject* topic_capsule = PyCapsule_New(
    topic, NULL, delete_topic_var);
  if (!topic_capsule) {
    PyErr_SetString(PyOpenDDS_Error, "Failed to Wrap Topic");
    return NULL;
  }
  PyObject_SetAttrString(pytopic, VAR_NAME, topic_capsule);

  // return None
  Py_RETURN_NONE;
}

/**
 * Callback for Python to Call when the Subscriber Capsule is Deleted
 */
void delete_subscriber_var(PyObject* subscriber_capsule)
{
  if (PyCapsule_CheckExact(subscriber_capsule)) {
    DDS::Subscriber_var subscriber = static_cast<DDS::Subscriber*>(
      PyCapsule_GetPointer(subscriber_capsule, NULL));
    subscriber = 0;
  }
}

/**
 * create_subscriber(subsciber: Subscriber, participant: DomainParticipant) -> None
 */
static PyObject* create_subscriber(PyObject* self, PyObject* args)
{
  // Get Arguments
  PyObject* pyparticipant;
  PyObject* pysubscriber;
  if (!PyArg_ParseTuple(args, "OO", &pysubscriber, &pyparticipant)) {
    PyErr_SetString(PyOpenDDS_Error, "Argument Parsing Failed");
    return NULL;
  }

  // Get DomainParticipant_var
  DDS::DomainParticipant* participant;
  PyObject* part_capsule = PyObject_GetAttrString(pyparticipant, VAR_NAME);
  bool valid_participant = part_capsule && PyCapsule_CheckExact(part_capsule);
  if (valid_participant) {
    participant = static_cast<DDS::DomainParticipant*>(
      PyCapsule_GetPointer(part_capsule, NULL));
  } else {
    PyErr_SetString(PyOpenDDS_Error,
      "Invalid Participant, Python Participant is Missing a Valid C++ Participant");
    return NULL;
  }

  // Create Subscriber
  DDS::Subscriber* subscriber = participant->create_subscriber(
    SUBSCRIBER_QOS_DEFAULT, 0, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (!subscriber) {
    PyErr_SetString(PyOpenDDS_Error, "Create Subscriber Failed");
    return NULL;
  }

  // Attach OpenDDS Subscriber to Subscriber Python Object
  PyObject* subscriber_capsule = PyCapsule_New(
    subscriber, NULL, delete_subscriber_var);
  if (!subscriber_capsule) {
    PyErr_SetString(PyOpenDDS_Error, "Failed to Wrap Subscriber");
    return NULL;
  }
  PyObject_SetAttrString(pysubscriber, VAR_NAME, subscriber_capsule);

  // return None
  Py_RETURN_NONE;
}

/**
 * Callback for Python to Call when the DataReader Capsule is Deleted
 */
void delete_reader_var(PyObject* reader_capsule)
{
  if (PyCapsule_CheckExact(reader_capsule)) {
    DDS::DataReader_var reader = static_cast<DDS::DataReader*>(
      PyCapsule_GetPointer(reader_capsule, NULL));
    reader = 0;
  }
}

/**
 * create_datareader(datareader: DataReader, subscriber: Subscriber, topic: Topic) -> None
 */
static PyObject* create_datareader(PyObject* self, PyObject* args)
{
  // Get Arguments
  PyObject* pydatareader;
  PyObject* pysubscriber;
  PyObject* pytopic;
  if (!PyArg_ParseTuple(args, "OOO", &pydatareader, &pysubscriber, &pytopic)) {
    PyErr_SetString(PyOpenDDS_Error, "Argument Parsing Failed");
    return NULL;
  }

  // Get Subscriber
  DDS::Subscriber* subscriber;
  PyObject* sub_capsule = PyObject_GetAttrString(pysubscriber, VAR_NAME);
  bool valid_subscriber = sub_capsule && PyCapsule_CheckExact(sub_capsule);
  if (valid_subscriber) {
    subscriber = static_cast<DDS::Subscriber*>(
      PyCapsule_GetPointer(sub_capsule, NULL));
  } else {
    PyErr_SetString(PyOpenDDS_Error,
      "Invalid Subscriber, Python Subscriber is Missing a Valid C++ Subscriber");
    return NULL;
  }

  // Get Topic
  DDS::Topic* topic;
  PyObject* topic_capsule = PyObject_GetAttrString(pytopic, VAR_NAME);
  bool valid_topic = topic_capsule && PyCapsule_CheckExact(topic_capsule);
  if (valid_topic) {
    topic = static_cast<DDS::Topic*>(
      PyCapsule_GetPointer(topic_capsule, NULL));
  } else {
    PyErr_SetString(PyOpenDDS_Error,
      "Invalid Topic, Python Topic is Missing a Valid C++ Topic");
    return NULL;
  }

  // Create DataReader
  DDS::DataReader* datareader = subscriber->create_datareader(
    topic, DATAREADER_QOS_DEFAULT, 0,
    OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (!datareader) {
    PyErr_SetString(PyOpenDDS_Error, "Create DataReader Failed");
    return NULL;
  }

  // Attach OpenDDS Subscriber to Subscriber Python Object
  PyObject* reader_capsule = PyCapsule_New(
    topic, NULL, delete_reader_var);
  if (!reader_capsule) {
    PyErr_SetString(PyOpenDDS_Error, "Failed to Wrap DataReader");
    return NULL;
  }
  PyObject_SetAttrString(pytopic, VAR_NAME, reader_capsule);

  // return None
  Py_RETURN_NONE;
}

static PyMethodDef pyopendds_Methods[] = {
  {
    "init_opendds", init_opendds, METH_VARARGS,
    "Initialize OpenDDS, using DDS::TheParticipantFactoryWithArgs"
  },
  { "create_participant", create_participant, METH_VARARGS, "" },
  { "participant_cleanup", participant_cleanup, METH_VARARGS, "" },
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
