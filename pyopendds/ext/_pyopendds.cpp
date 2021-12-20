#include <pyopendds/common.hpp> // Must always be first include

#include <dds/DCPS/transport/framework/TransportRegistry.h>
#include <dds/DCPS/transport/framework/TransportConfig.h>
#include <dds/DCPS/transport/framework/TransportInst.h>

#include <dds/DdsDcpsInfrastructureC.h>
#include <dds/DdsDcpsCoreC.h>
#include <dds/DCPS/Service_Participant.h>
#include <dds/DCPS/Marked_Default_Qos.h>
#include <dds/DCPS/WaitSet.h>
#include <dds/Version.h>

#include <ace/Init_ACE.h>

using namespace pyopendds;

PyObject* Errors::pyopendds_ = nullptr;
PyObject* Errors::PyOpenDDS_Error_ = nullptr;
PyObject* Errors::ReturnCodeError_ = nullptr;

namespace {

PyObject* opendds_version_str(PyObject*, PyObject*)
{
  return PyUnicode_FromString(OPENDDS_VERSION);
}

PyObject* opendds_version_tuple(PyObject*, PyObject*)
{
  return Py_BuildValue("(I,I,I)",
    unsigned(OPENDDS_MAJOR_VERSION),
    unsigned(OPENDDS_MINOR_VERSION),
    unsigned(OPENDDS_MICRO_VERSION));
}

PyObject* opendds_version_dict(PyObject*, PyObject*)
{
  return Py_BuildValue("{s:I,s:I,s:I,s:s,s:I}",
    "major",
    OPENDDS_MAJOR_VERSION,
    "minor",
    OPENDDS_MINOR_VERSION,
    "micro",
    OPENDDS_MICRO_VERSION,
    "metadata",
    OPENDDS_VERSION_METADATA,
    "is_release",
    OPENDDS_IS_RELEASE);
}

/// Global Participant Factory
DDS::DomainParticipantFactory_var participant_factory;

/**
 * init_opendds_impl(*args[str], **kw) -> None
 *
 * Initialize participant_factory by passing args to
 * TheParticipantFactoryWithArgs. Also perform some custom configuration based
 * on keyword arguments:
 *
 * default_rtps: bool=True
 *   Set default transport and discovery to RTPS unless default_rtps=False was
 *   passed.
 */
PyObject* init_opendds_impl(PyObject* self, PyObject* args, PyObject* kw)
{
#ifdef _WIN32
  // On Windows it apparently doesn't call this automatically. If not called it
  // can cause an access violation when trying to use the "managed objects" in
  // ACE.
  ACE::init();
#endif

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
    return PyErr_NoMemory();
  }
  for (int i = 0; i < argc; i++) {
    // Get str object
    Ref obj{PySequence_GetItem(args, i)};
    if (!obj) {
      return nullptr;
    }
    Ref string_obj{PyObject_Str(*obj)};
    if (!string_obj) {
      return nullptr;
    }

    // Get UTF8 char* String
    ssize_t string_len;
    const char* string = PyUnicode_AsUTF8AndSize(*string_obj, &string_len);
    if (!string) {
      return nullptr;
    }

    // Copy It
    char* duplicate = new char[string_len + 1];
    if (!duplicate) {
      return PyErr_NoMemory();
    }
    duplicate[string_len] = '\0';
    argv[i] = original_argv[i] = strncpy(duplicate, string, string_len);
  }

  /*
   * Process default_rtps
   */
  bool default_rtps = true;
  Ref default_rtps_obj{PyMapping_GetItemString(kw, "default_rtps")};
  if (default_rtps_obj) {
    int result = PyObject_IsTrue(*default_rtps_obj);
    if (result == -1) {
      return nullptr;
    }
    default_rtps = result;
  } else {
    PyErr_Clear();
  }
  if (default_rtps) {
    TheServiceParticipant->set_default_discovery(OpenDDS::DCPS::Discovery::DEFAULT_RTPS);
    OpenDDS::DCPS::TransportConfig_rch transport_config =
      TheTransportRegistry->create_config("default_rtps_transport_config");
    OpenDDS::DCPS::TransportInst_rch transport_inst =
      TheTransportRegistry->create_inst("default_rtps_transport", "rtps_udp");
    transport_config->instances_.push_back(transport_inst);
    TheTransportRegistry->global_config(transport_config);
  }

  // Initialize OpenDDS
  participant_factory = TheParticipantFactoryWithArgs(argc, argv);
  if (!participant_factory) {
    PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to Initialize OpenDDS");
    return nullptr;
  }

  // Cleanup args
  for (int i = 0; i < original_argc; i++) {
    delete original_argv[i];
  }
  delete[] original_argv;
  delete[] argv;

  Py_RETURN_NONE;
}

/**
 * Callback for Python to Call when the Python Participant is Deleted
 */
void delete_participant_var(PyObject* part_capsule)
{
  if (PyCapsule_CheckExact(part_capsule)) {
    DDS::DomainParticipant_var participant =
      static_cast<DDS::DomainParticipant*>(PyCapsule_GetPointer(part_capsule, nullptr));
    participant = nullptr;
  }
}

/**
 * create_participant(participant: DomainParticipant, domain: int) -> None
 */
PyObject* create_participant(PyObject* self, PyObject* args)
{
  Ref pyparticipant;
  unsigned domain;
  if (!PyArg_ParseTuple(args, "OI", &*pyparticipant, &domain)) {
    return nullptr;
  }
  pyparticipant++;

  // Create Participant
  DDS::DomainParticipantQos qos;
  participant_factory->get_default_participant_qos(qos);
  DDS::DomainParticipant* participant = participant_factory->create_participant(
    domain, qos, DDS::DomainParticipantListener::_nil(), OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (!participant) {
    PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to Create Participant");
    return nullptr;
  }

  // Attach OpenDDS Participant to Participant Python Object
  if (set_capsule(*pyparticipant, participant, delete_participant_var)) {
    return nullptr;
  }

  Py_RETURN_NONE;
}

PyObject* participant_cleanup(PyObject* self, PyObject* args)
{
  Ref pyparticipant;
  if (!PyArg_ParseTuple(args, "O", &*pyparticipant)) {
    return nullptr;
  }
  pyparticipant++;

  // Get DomainParticipant_var
  DDS::DomainParticipant* participant = get_capsule<DDS::DomainParticipant>(*pyparticipant);
  if (!participant) {
    return nullptr;
  }

  participant->delete_contained_entities();
  Py_RETURN_NONE;
}

/**
 * Callback for Python to Call when the Topic Capsule is Deleted
 */
void delete_topic_var(PyObject* topic_capsule)
{
  if (PyCapsule_CheckExact(topic_capsule)) {
    DDS::Topic_var topic = static_cast<DDS::Topic*>(PyCapsule_GetPointer(topic_capsule, nullptr));
    topic = nullptr;
  }
}

/*
 * create_topic(topic: Topic, participant: DomainParticipant, topic_name: str, topic_type: str) -> None
 *
 * Assumes all the arguments are the types listed above and the participant has
 * a OpenDDS DomainParticipant with the type named by topic_type has already
 * been registered with it.
 */
PyObject* create_topic(PyObject* self, PyObject* args)
{
  Ref pytopic;
  Ref pyparticipant;
  char* name;
  char* type;
  if (!PyArg_ParseTuple(args, "OOss", &*pytopic, &*pyparticipant, &name, &type)) {
    return nullptr;
  }
  pytopic++;
  pyparticipant++;

  // Get DomainParticipant
  DDS::DomainParticipant* participant = get_capsule<DDS::DomainParticipant>(*pyparticipant);
  if (!participant) {
    return nullptr;
  }

  // Create Topic
  DDS::Topic* topic = participant->create_topic(
    name, type, TOPIC_QOS_DEFAULT, nullptr, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (!topic) {
    PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to Create Topic");
    return nullptr;
  }

  // Attach OpenDDS Topic to Topic Python Object
  if (set_capsule(*pytopic, topic, delete_topic_var)) {
    return nullptr;
  }

  Py_RETURN_NONE;
}

/**
 * Callback for Python to Call when the Subscriber Capsule is Deleted
 */
void delete_subscriber_var(PyObject* subscriber_capsule)
{
  if (PyCapsule_CheckExact(subscriber_capsule)) {
    DDS::Subscriber_var subscriber =
      static_cast<DDS::Subscriber*>(PyCapsule_GetPointer(subscriber_capsule, nullptr));
    subscriber = nullptr;
  }
}

/**
 * create_subscriber(subscriber: Subscriber, participant: DomainParticipant) -> None
 */
PyObject* create_subscriber(PyObject* self, PyObject* args)
{
  Ref pyparticipant;
  Ref pysubscriber;
  if (!PyArg_ParseTuple(args, "OO", &*pysubscriber, &*pyparticipant)) {
    return nullptr;
  }
  pyparticipant++;
  pysubscriber++;

  // Get DomainParticipant_var
  DDS::DomainParticipant* participant = get_capsule<DDS::DomainParticipant>(*pyparticipant);
  if (!participant) {
    return nullptr;
  }

  // Create Subscriber
  DDS::Subscriber* subscriber = participant->create_subscriber(
    SUBSCRIBER_QOS_DEFAULT, nullptr, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (!subscriber) {
    PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to Create Subscriber");
    return nullptr;
  }

  // Attach OpenDDS Subscriber to Subscriber Python Object
  if (set_capsule(*pysubscriber, subscriber, delete_subscriber_var)) {
    return nullptr;
  }

  Py_RETURN_NONE;
}

/**
 * Callback for Python to Call when the Publisher Capsule is Deleted
 */
void delete_publisher_var(PyObject* publisher_capsule)
{
  if (PyCapsule_CheckExact(publisher_capsule)) {
    DDS::Publisher_var publisher =
      static_cast<DDS::Publisher*>(PyCapsule_GetPointer(publisher_capsule, nullptr));
    publisher = nullptr;
  }
}

/**
 * create_publisher(publisher: Publisher, participant: DomainParticipant) -> None
 */
PyObject* create_publisher(PyObject* self, PyObject* args)
{
  Ref pyparticipant;
  Ref pypublisher;
  if (!PyArg_ParseTuple(args, "OO", &*pypublisher, &*pyparticipant)) {
    return nullptr;
  }
  pyparticipant++;
  pypublisher++;

  // Get DomainParticipant_var
  DDS::DomainParticipant* participant = get_capsule<DDS::DomainParticipant>(*pyparticipant);
  if (!participant) {
    return nullptr;
  }

  // Create Publisher
  DDS::Publisher* publisher = participant->create_publisher(
    PUBLISHER_QOS_DEFAULT, nullptr, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (!publisher) {
    PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to Create Publisher");
    return nullptr;
  }

  // Attach OpenDDS Publisher to Publisher Python Object
  if (set_capsule(*pypublisher, publisher, delete_publisher_var)) {
    return nullptr;
  }

  Py_RETURN_NONE;
}

/**
 * Callback for Python to Call when the DataReader Capsule is Deleted
 */
void delete_datareader_var(PyObject* reader_capsule)
{
  if (PyCapsule_CheckExact(reader_capsule)) {
    DDS::DataReader_var reader =
      static_cast<DDS::DataReader*>(PyCapsule_GetPointer(reader_capsule, nullptr));
    reader = nullptr;
  }
}

/**
 * create_datareader(datareader: DataReader, subscriber: Subscriber, topic: Topic) -> None
 */
PyObject* create_datareader(PyObject* self, PyObject* args)
{
  Ref pydatareader;
  Ref pysubscriber;
  Ref pytopic;
  if (!PyArg_ParseTuple(args, "OOO", &*pydatareader, &*pysubscriber, &*pytopic)) {
    return nullptr;
  }
  pydatareader++;
  pysubscriber++;
  pytopic++;

  // Get Subscriber
  DDS::Subscriber* subscriber = get_capsule<DDS::Subscriber>(*pysubscriber);
  if (!subscriber) {
    return nullptr;
  }

  // Get Topic
  DDS::Topic* topic = get_capsule<DDS::Topic>(*pytopic);
  if (!topic) {
    return nullptr;
  }

  // Create DataReader
  DDS::DataReader* datareader = subscriber->create_datareader(
    topic, DATAREADER_QOS_DEFAULT, nullptr, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
  if (!datareader) {
    PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to Create DataReader");
    return nullptr;
  }

  // Attach OpenDDS DataReader to DataReader Python Object
  if (set_capsule(*pydatareader, datareader, delete_datareader_var)) {
    return nullptr;
  }

  Py_RETURN_NONE;
}

/**
 * datareader_wait_for(
 *     datareader: DataReader, status: StatusKind,
 *     seconds: int, nanoseconds: int) -> None
 */
PyObject* datareader_wait_for(PyObject* self, PyObject* args)
{
  Ref pydatareader;
  unsigned status;
  int seconds;
  unsigned nanoseconds;
  if (!PyArg_ParseTuple(args, "OIiI", &*pydatareader, &status, &seconds, &nanoseconds)) {
    return nullptr;
  }
  pydatareader++;

  // Get DataReader
  DDS::DataReader* reader = get_capsule<DDS::DataReader>(*pydatareader);
  if (!reader) {
    return nullptr;
  }

  // Wait
  DDS::StatusCondition_var condition = reader->get_statuscondition();
  condition->set_enabled_statuses(status);
  DDS::WaitSet_var waitset = new DDS::WaitSet;
  if (!waitset) {
    return PyErr_NoMemory();
  }
  waitset->attach_condition(condition);
  DDS::ConditionSeq active;
  DDS::Duration_t max_duration = {seconds, nanoseconds};
  if (Errors::check_rc(waitset->wait(active, max_duration))) {
    return nullptr;
  }

  Py_RETURN_NONE;
}

/// Documentation for Internal Python Objects
const char* internal_docstr = "Internal to PyOpenDDS, not for use directly!";

PyMethodDef pyopendds_Methods[] = {
  {"opendds_version_str", opendds_version_str, METH_NOARGS, internal_docstr},
  {"opendds_version_tuple", opendds_version_tuple, METH_NOARGS, internal_docstr},
  {"opendds_version_dict", opendds_version_dict, METH_NOARGS, internal_docstr},
  {
    "init_opendds_impl",
    reinterpret_cast<PyCFunction>(init_opendds_impl),
    METH_VARARGS | METH_KEYWORDS,
    internal_docstr,
  },
  {"create_participant", create_participant, METH_VARARGS, internal_docstr},
  {"participant_cleanup", participant_cleanup, METH_VARARGS, internal_docstr},
  {"create_subscriber", create_subscriber, METH_VARARGS, internal_docstr},
  {"create_publisher", create_publisher, METH_VARARGS, internal_docstr},
  {"create_topic", create_topic, METH_VARARGS, internal_docstr},
  {"create_datareader", create_datareader, METH_VARARGS, internal_docstr},
  {"datareader_wait_for", datareader_wait_for, METH_VARARGS, internal_docstr},
  {nullptr, nullptr, 0, nullptr},
};

PyModuleDef pyopendds_Module = {
  PyModuleDef_HEAD_INIT,
  "_pyopendds",
  "Internal Python Bindings for OpenDDS",
  -1, // Global State Module, because OpenDDS uses Singletons
  pyopendds_Methods,
};

} // Anonymous Namespace

PyMODINIT_FUNC PyInit__pyopendds()
{
  // Create _pyopendds
  PyObject* native_module = PyModule_Create(&pyopendds_Module);
  if (!native_module || Errors::cache()) {
    return nullptr;
  }

  return native_module;
}
