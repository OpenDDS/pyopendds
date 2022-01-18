#include <pyopendds/common.hpp> // Must always be first include

#include <dds/DCPS/transport/framework/TransportRegistry.h>
#include <dds/DCPS/transport/framework/TransportConfig.h>
#include <dds/DCPS/transport/framework/TransportInst.h>
#include "dds/DCPS/transport/shmem/ShmemInst.h"

#include <dds/DdsDcpsInfrastructureC.h>
#include <dds/DdsDcpsCoreC.h>
#include <dds/DCPS/Service_Participant.h>
#include <dds/DCPS/Marked_Default_Qos.h>
#include <dds/DCPS/WaitSet.h>

#include <chrono>
#include <thread>


using namespace pyopendds;

PyObject* Errors::pyopendds_ = nullptr;
PyObject* Errors::PyOpenDDS_Error_ = nullptr;
PyObject* Errors::ReturnCodeError_ = nullptr;

namespace {

class DataReaderListenerImpl : public virtual OpenDDS::DCPS::LocalObject<DDS::DataReaderListener> {

public:
    DataReaderListenerImpl(PyObject * self, PyObject *callback);

    

    virtual void on_requested_deadline_missed(
        DDS::DataReader_ptr reader,
        const DDS::RequestedDeadlineMissedStatus& status) { }

    virtual void on_requested_incompatible_qos(
        DDS::DataReader_ptr reader,
        const DDS::RequestedIncompatibleQosStatus& status) { }

    virtual void on_sample_rejected(
        DDS::DataReader_ptr reader,
        const DDS::SampleRejectedStatus& status) { }

    virtual void on_liveliness_changed(
        DDS::DataReader_ptr reader,
        const DDS::LivelinessChangedStatus& status) { }

    virtual void on_data_available(
        DDS::DataReader_ptr reader);

    virtual void on_subscription_matched(
        DDS::DataReader_ptr reader,
        const DDS::SubscriptionMatchedStatus& status) { }

    virtual void on_sample_lost(
        DDS::DataReader_ptr reader,
        const DDS::SampleLostStatus& status) { }

private:
    PyObject *_callback;
    PyObject * _self;
};

DataReaderListenerImpl::DataReaderListenerImpl(PyObject* self, PyObject* callback) :
    OpenDDS::DCPS::LocalObject<DDS::DataReaderListener>()
{
    _self = self;
    Py_XINCREF(_self);
    _callback = callback;
    Py_XINCREF(_callback);
}

void DataReaderListenerImpl::on_data_available(DDS::DataReader_ptr reader)
{
    PyObject *callable = _callback;
    PyObject *result = NULL;

    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();
    try {
        if (PyCallable_Check(callable)) {
            result = PyObject_CallFunctionObjArgs(callable, nullptr);
            if (result == NULL) {
                PyErr_Print();
            }
            Py_XDECREF(result);
        } else {
            throw Exception("Pyobject is not a callable", PyExc_TypeError);
        }
    } catch (Exception& e) {
        //    Py_XDECREF(callable);
        PyGILState_Release(gstate);
        throw e;
    }
    //Py_XDECREF(callable);
    PyGILState_Release(gstate);
}

/// Global Participant Factory
DDS::DomainParticipantFactory_var participant_factory;

static int numParticipant = 0;

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
    /*
    * In addition to the need to convert the arguments into an argv array,
    * OpenDDS will mess with argv and argc so we need to create copies that we
    * can cleanup properly afterwords.
    */
    int original_argc = PySequence_Size(args);
    int argc = original_argc;
    char** original_argv = new char*[argc];
    char** argv = new char*[argc];
    if (!original_argv || !argv) return PyErr_NoMemory();

    for (int i = 0; i < argc; i++) {
        // Get str object
        Ref obj{PySequence_GetItem(args, i)};
        if (!obj) return nullptr;
        Ref string_obj{PyObject_Str(*obj)};
        if (!string_obj) return nullptr;

        // Get UTF8 char* String
        ssize_t string_len;
        const char* string = PyUnicode_AsUTF8AndSize(*string_obj, &string_len);
        if (!string) return nullptr;

        // Copy It
        char* duplicate = new char[string_len + 1];
        if (!duplicate) return PyErr_NoMemory();
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
        if (result == -1) return nullptr;
        default_rtps = result;
    } else {
        PyErr_Clear();
    }
    if (default_rtps) {
        TheServiceParticipant->set_default_discovery(OpenDDS::DCPS::Discovery::DEFAULT_RTPS);
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

    delete [] original_argv;
    delete [] argv;

    Py_RETURN_NONE;
}

/**
* Callback for Python to Call when the Python Participant is Deleted
*/
void delete_participant_var(PyObject* part_capsule)
{
    if (PyCapsule_CheckExact(part_capsule)) {
        DDS::DomainParticipant_var participant = static_cast<DDS::DomainParticipant*>(
            PyCapsule_GetPointer(part_capsule, nullptr));

        if (participant) {
            //participant->delete_contained_entities();
            numParticipant--;
            participant = nullptr;
        }
    }
}

/**
* create_participant(participant: DomainParticipant, domain: int) -> None
*/
PyObject* create_participant(PyObject* self, PyObject* args)
{
    Ref pyparticipant;
    unsigned int domain;
    int isRtpstransport;
    if (!PyArg_ParseTuple(args, "OIi", &*pyparticipant, &domain, &isRtpstransport)) {
        return nullptr;
    }
    pyparticipant++;
    numParticipant++;
    
    OpenDDS::DCPS::TransportConfig_rch transport_config;
    OpenDDS::DCPS::TransportInst_rch transport_inst;
    if (isRtpstransport==1){
        transport_config =
        TheTransportRegistry->create_config("default_rtps_transport_config_"+ std::to_string(domain));

        transport_inst =
        TheTransportRegistry->create_inst("default_rtps_transport_"+std::to_string(domain), "rtps_udp");

    }else{
        // Create SHMEM transport config for this domainId
        transport_config = TheTransportRegistry->create_config("default_shmem_transport_config_"+ std::to_string(domain));
        transport_inst =TheTransportRegistry->create_inst("default_shmem_transport_"+std::to_string(domain), "shmem");
        OpenDDS::DCPS::ShmemInst * shmemInst = static_cast<OpenDDS::DCPS::ShmemInst *>(transport_inst.get());
        if(shmemInst != nullptr) {
            shmemInst->pool_size_ = 67108864; // (4x 4K image size);
            shmemInst->datalink_control_size_ = 8192;
        }
    }
    transport_config->instances_.push_back(transport_inst);
    TheTransportRegistry->domain_default_config(domain, transport_config);
   
    // Create Participant
    DDS::DomainParticipantQos qos;
    participant_factory->get_default_participant_qos(qos);

    DDS::DomainParticipant* participant = participant_factory->create_participant(
        domain, qos, DDS::DomainParticipantListener::_nil(),
        OpenDDS::DCPS::DEFAULT_STATUS_MASK);

    if (!participant) {
        PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to Create Participant");
        numParticipant--;
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
    DDS::DomainParticipant* participant =
        get_capsule<DDS::DomainParticipant>(*pyparticipant);

    if (!participant) return nullptr;
    
    numParticipant--;
    // std::cout<<numParticipant<<"\n" ;
   
    participant->delete_contained_entities();
    participant_factory->delete_participant(participant);

    if (numParticipant == 0)
    {
        
        TheServiceParticipant->shutdown();
    }
    

    Py_RETURN_NONE;
}

/**
* Callback for Python to Call when the Topic Capsule is Deleted
*/
void delete_topic_var(PyObject* topic_capsule)
{
    if (PyCapsule_CheckExact(topic_capsule)) {
        DDS::Topic_var topic = static_cast<DDS::Topic*>(PyCapsule_GetPointer(topic_capsule, nullptr));
        if (topic) topic = nullptr;
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
    if (!PyArg_ParseTuple(args, "OOss",
    &*pytopic, &*pyparticipant, &name, &type)) {
        return nullptr;
    }
    pytopic++;
    pyparticipant++;

    // Get DomainParticipant
    DDS::DomainParticipant* participant =
        get_capsule<DDS::DomainParticipant>(*pyparticipant);
    if (!participant) return nullptr;

    // Create Topic
    DDS::Topic* topic = participant->create_topic(
        name, type, TOPIC_QOS_DEFAULT, nullptr,
        OpenDDS::DCPS::DEFAULT_STATUS_MASK);

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
        DDS::Subscriber_var subscriber = static_cast<DDS::Subscriber*>(
            PyCapsule_GetPointer(subscriber_capsule, nullptr));
        if (subscriber) subscriber = nullptr;
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
    DDS::DomainParticipant* participant =
        get_capsule<DDS::DomainParticipant>(*pyparticipant);
    if (!participant) return nullptr;

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
        DDS::Publisher_var publisher = static_cast<DDS::Publisher*>(
            PyCapsule_GetPointer(publisher_capsule, nullptr));
       if (publisher) publisher = nullptr;
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
    DDS::DomainParticipant* participant =
        get_capsule<DDS::DomainParticipant>(*pyparticipant);
    if (!participant) return nullptr;

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
        DDS::DataReader_var reader = static_cast<DDS::DataReader*>(
            PyCapsule_GetPointer(reader_capsule, nullptr));

        if (reader) {
            DDS::DataReaderListener_ptr listener = reader->get_listener();
            /*DDS::DataReader::_narrow(reader)->get_listener();*/
            free(listener);
            listener = nullptr;
            reader = nullptr;
        }
    }
}


bool update_writer_qos(PyObject* pyQos, DDS::DataWriterQos &qos)
{
    Ref pydurability;
    Ref pyreliability;
    Ref pyhistory;
    Ref pydurabilityKind;
    Ref pyreliabilityKind;
    Ref pyhistoryKind;
    Ref pyhistorydepth;

    pydurability = PyObject_GetAttrString(pyQos, "durability");
    if (!pydurability) return false;
    pydurability ++;

    pyreliability = PyObject_GetAttrString(pyQos, "reliability");
    if (!pyreliability) return false;
    pyreliability ++;

    pyhistory = PyObject_GetAttrString(pyQos, "history");
    if (!pyhistory) return false;
    pyhistory ++;

    pydurabilityKind = PyObject_GetAttrString(*pydurability, "kind");
    if (!pydurabilityKind) return false;
    pydurabilityKind ++;
    qos.durability.kind = (DDS::DurabilityQosPolicyKind) PyLong_AsLong(*pydurabilityKind);

    pyreliabilityKind = PyObject_GetAttrString(*pyreliability, "kind");
    if (!pyreliabilityKind) return false;
    pyreliabilityKind ++;
    qos.reliability.kind = (DDS::ReliabilityQosPolicyKind) PyLong_AsLong(*pyreliabilityKind);


    pyhistoryKind = PyObject_GetAttrString(*pyhistory, "kind");
    if (!pyhistoryKind) return false;
    pyhistoryKind ++;
    qos.history.kind = (DDS::HistoryQosPolicyKind) PyLong_AsLong(*pyhistoryKind);

    pyhistorydepth = PyObject_GetAttrString(*pyhistory, "depth");
    if (!pyhistorydepth) return false;
    pyhistorydepth ++;
    qos.history.depth =  PyLong_AsLong(*pyhistorydepth);
    

    return true;
}

bool update_reader_qos(PyObject* pyQos, DDS::DataReaderQos &qos)
{
        Ref pydurability;
        Ref pyreliability;
        Ref pyhistory;
        Ref pydurabilityKind;
        Ref pyreliabilityKind;
        Ref pyhistoryKind;
        Ref pyhistorydepth;
        Ref pyreliabilitymax;

    
        // Create Qos for the data writer according to the spec
        pydurability = PyObject_GetAttrString(pyQos, "durability");
        if (!pydurability)
        { 
            return false;
        }
        pydurability ++;
        
        pyreliability = PyObject_GetAttrString(pyQos, "reliability");
        if (!pyreliability) return false;
        pyreliability ++;

        pyhistory = PyObject_GetAttrString(pyQos, "history");
        if (!pyhistory) return false;
        pyhistory ++;

        pydurabilityKind = PyObject_GetAttrString(*pydurability, "kind");
        if (!pydurabilityKind) return false;
        pydurabilityKind ++;
        qos.durability.kind = (DDS::DurabilityQosPolicyKind) PyLong_AsLong(*pydurabilityKind);

        pyreliabilityKind = PyObject_GetAttrString(*pyreliability, "kind");
        if (!pyreliabilityKind) return false;
        pyreliabilityKind ++;
        qos.reliability.kind = (DDS::ReliabilityQosPolicyKind) PyLong_AsLong(*pyreliabilityKind);
        
        pyreliabilitymax = PyObject_GetAttrString(*pyreliability, "max_blocking_time");
        if (!pyreliabilitymax) return false;
        pyreliabilitymax ++;
        qos.history.depth =  PyLong_AsLong(*pyreliabilitymax);

        pyhistoryKind = PyObject_GetAttrString(*pyhistory, "kind");
        if (!pyhistoryKind) return false;
        pyhistoryKind ++;

        qos.history.kind = (DDS::HistoryQosPolicyKind) PyLong_AsLong(*pyhistoryKind);

        pyhistorydepth = PyObject_GetAttrString(*pyhistory, "depth");
        if (!pyhistorydepth) return false;
        pyhistorydepth ++;
        qos.history.depth =  PyLong_AsLong(*pyhistorydepth);
       
        return true;
}
/**
* create_datareader(datareader: DataReader, subscriber: Subscriber, topic: Topic, listener: pyObject) -> None
*/
PyObject* create_datareader(PyObject* self, PyObject* args )
{
    Ref pydatareader;
    Ref pysubscriber;
    Ref pytopic;
    Ref pycallback;
    Ref pyqos;

    if (!PyArg_ParseTuple(args, "OOOOO", 
    &*pydatareader, &*pysubscriber, &*pytopic, &*pycallback,&*pyqos )) {
        return nullptr;
    }
    pydatareader++;
    pysubscriber++;
    pytopic++;
    pycallback++;
    pyqos++; 


    // Get Subscriber
    DDS::Subscriber* subscriber = get_capsule<DDS::Subscriber>(*pysubscriber);
    if (!subscriber) return nullptr;

    // Get Topic
    DDS::Topic* topic = get_capsule<DDS::Topic>(*pytopic);
    if (!topic) return nullptr;

    DataReaderListenerImpl * listener = nullptr;
    if (*pycallback != Py_None) {
        if (PyCallable_Check(*pycallback)) {
            listener = new DataReaderListenerImpl(*pydatareader, *pycallback);
        }
        else {
            throw Exception("Callback provided is not a callable object", PyExc_TypeError);
        }
    }

    
    // Create QoS
    DDS::DataReaderQos qos;
     
    subscriber->get_default_datareader_qos(qos);
    bool isgoodqos = update_reader_qos(*pyqos,qos); 
    // Create DataReader
    DDS::DataReader* datareader = subscriber->create_datareader(
       topic, qos, listener,
         OpenDDS::DCPS::DEFAULT_STATUS_MASK);

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
* Callback for Python to Call when the DataWriter Capsule is Deleted
*/
void delete_datawriter_var(PyObject* writer_capsule)
{
    if (PyCapsule_CheckExact(writer_capsule)) {
        DDS::DataWriter_var writer = static_cast<DDS::DataWriter*>(
            PyCapsule_GetPointer(writer_capsule, nullptr));
       if (writer) writer = nullptr;
    }
}

/**
* create_datawriter(datawriter: DataWriter, publisher: Publisher, topic: Topic) -> None
*/
PyObject* create_datawriter(PyObject* self, PyObject* args)
{
    Ref pydatawriter;
    Ref pypublisher;
    Ref pytopic;
    Ref pyqos;
    if (!PyArg_ParseTuple(args, "OOOO",
    &*pydatawriter, &*pypublisher, &*pytopic,&*pyqos)) {
        return nullptr;
    }
    pydatawriter++;
    pypublisher++;
    pytopic++;
    pyqos++;

    // Get Publisher
    DDS::Publisher* publisher = get_capsule<DDS::Publisher>(*pypublisher);
    if (!publisher) return nullptr;

    // Get Topic
    DDS::Topic* topic = get_capsule<DDS::Topic>(*pytopic);
    if (!topic) return nullptr;

    // Create QoS
    DDS::DataWriterQos qos;
    publisher->get_default_datawriter_qos(qos);
    qos.reliability.kind = DDS::RELIABLE_RELIABILITY_QOS;

    bool isgoodwriterqos = update_writer_qos(*pyqos,qos);
    // Create DataWriter
    DDS::DataWriter* datawriter = publisher->create_datawriter(
        topic, qos, nullptr,
        OpenDDS::DCPS::DEFAULT_STATUS_MASK);

    if (!datawriter) {
        PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to Create DataWriter");
        return nullptr;
    }

    // Attach OpenDDS DataWriter to DataWriter Python Object
    if (set_capsule(*pydatawriter, datawriter, delete_datawriter_var)) {
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
    if (!PyArg_ParseTuple(args, "OIiI",
    &*pydatareader, &status, &seconds, &nanoseconds)) {
        return nullptr;
    }
    pydatareader++;

    // Get DataReader
    DDS::DataReader* reader = get_capsule<DDS::DataReader>(*pydatareader);
    if (!reader) {
        PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to retrieve DataReader Capsule");
        return nullptr;
    }

    // Wait
    DDS::StatusCondition_var condition = reader->get_statuscondition();
    condition->set_enabled_statuses(status);

#ifndef __APPLE__
    DDS::WaitSet_var waitset = new DDS::WaitSet;
    if (!waitset) return PyErr_NoMemory();
    waitset->attach_condition(condition);
    DDS::ConditionSeq active;
    DDS::Duration_t max_duration = {seconds, nanoseconds};
    if (Errors::check_rc(waitset->wait(active, max_duration))) return nullptr;
#else
    // TODO: wait() causes segmentation fault
    // TODO: fallback to naive implementation
    auto t_now = std::chrono::steady_clock::now();
    auto t_secs = std::chrono::seconds(seconds);
    auto t_nanosecs = std::chrono::nanoseconds(nanoseconds);
    auto t_timeout = t_now + t_secs + t_nanosecs;

    while (t_now < t_timeout) {
        DDS::SubscriptionMatchedStatus matches;
        if (reader->get_subscription_matched_status(matches) != DDS::RETCODE_OK) {
            PyErr_SetString(Errors::PyOpenDDS_Error(), "get_subscription_matched_status failed");
            return nullptr;
        }
        if (matches.current_count >= 1) {
            break;
        }
        // wait for 1 second anyway, and update clock
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
        t_now = std::chrono::steady_clock::now();
    }
#endif
    Py_RETURN_NONE;
}

/**
* datawriter_wait_for(
*     datawriter: DataWriter, status: StatusKind,
*     seconds: int, nanoseconds: int) -> None
*/
PyObject* datawriter_wait_for(PyObject* self, PyObject* args)
{
    Ref pydatawriter;
    unsigned status;
    int seconds;
    unsigned nanoseconds;
    if (!PyArg_ParseTuple(args, "OIiI",
    &*pydatawriter, &status, &seconds, &nanoseconds)) {
        return nullptr;
    }
    pydatawriter++;

    // Get DataWriter
    DDS::DataWriter* writer = get_capsule<DDS::DataWriter>(*pydatawriter);
    if (!writer) {
        PyErr_SetString(Errors::PyOpenDDS_Error(), "Failed to retrieve DataWriter Capsule");
        return nullptr;
    }

    // Wait
    DDS::StatusCondition_var condition = writer->get_statuscondition();
    condition->set_enabled_statuses(status);

#ifndef __APPLE__
    DDS::WaitSet_var waitset = new DDS::WaitSet;
    if (!waitset) return PyErr_NoMemory();
    waitset->attach_condition(condition);
    DDS::ConditionSeq active;
    DDS::Duration_t max_duration = {seconds, nanoseconds};
    if (Errors::check_rc(waitset->wait(active, max_duration))) return nullptr;
#else
    // TODO: wait() causes segmentation fault
    // TODO: fallback to naive implementation
    auto t_now = std::chrono::steady_clock::now();
    auto t_secs = std::chrono::seconds(seconds);
    auto t_nanosecs = std::chrono::nanoseconds(nanoseconds);
    auto t_timeout = t_now + t_secs + t_nanosecs;

    while (t_now < t_timeout) {
        DDS::PublicationMatchedStatus matches;
        if (writer->get_publication_matched_status(matches) != DDS::RETCODE_OK) {
            PyErr_SetString(Errors::PyOpenDDS_Error(), "get_publication_matched_status failed");
            return nullptr;
        }
        if (matches.current_count >= 1) {
            break;
        }
        // wait for 1 second anyway, and update clock
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
        t_now = std::chrono::steady_clock::now();
    }
#endif
    Py_RETURN_NONE;
}





/// Documentation for Internal Python Objects
const char* internal_docstr = "Internal to PyOpenDDS, not for use directly!";

PyMethodDef pyopendds_Methods[] = {
    { "init_opendds_impl", reinterpret_cast<PyCFunction>(init_opendds_impl),
        METH_VARARGS | METH_KEYWORDS, internal_docstr
    },
    { "create_participant", create_participant, METH_VARARGS, internal_docstr },
    { "participant_cleanup", participant_cleanup, METH_VARARGS, internal_docstr },
    { "create_subscriber", create_subscriber, METH_VARARGS, internal_docstr },
    { "create_publisher", create_publisher, METH_VARARGS, internal_docstr },
    { "create_topic", create_topic, METH_VARARGS, internal_docstr },
    { "create_datareader", create_datareader, METH_VARARGS, internal_docstr },
    { "create_datawriter", create_datawriter, METH_VARARGS, internal_docstr },
    { "datareader_wait_for", datareader_wait_for, METH_VARARGS, internal_docstr },
    { "datawriter_wait_for", datawriter_wait_for, METH_VARARGS, internal_docstr },
    { nullptr, nullptr, 0, nullptr }
};

PyModuleDef pyopendds_Module = {
    PyModuleDef_HEAD_INIT,
    "_pyopendds", "Internal Python Bindings for OpenDDS",
    -1, // Global State Module, because OpenDDS uses Singletons
    pyopendds_Methods
};

} // Anonymous Namespace


PyMODINIT_FUNC PyInit__pyopendds()
{
    // Create _pyopendds
    PyObject* native_module = PyModule_Create(&pyopendds_Module);

    if (!native_module || Errors::cache())
        return nullptr;

    return native_module;
}
