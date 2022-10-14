#ifndef PYOPENDDS_TOPICTYPE_HEADER
#define PYOPENDDS_TOPICTYPE_HEADER

#include <Python.h>

#include <dds/DCPS/TypeSupportImpl.h>
#include <dds/DCPS/WaitSet.h>
#include <dds/DdsDcpsDomainC.h>

#include <map>
#include <memory>
#include <stdexcept>

namespace pyopendds {

template<typename T>
class Type;
class TopicTypeBase;

class Global {
public:
    typedef std::shared_ptr<TopicTypeBase> Ptr;
    typedef std::map<PyObject*, Ptr> TopicTypes;

    TopicTypes& topic_types_() { return _d; }

private:
    TopicTypes _d;
};

class TopicTypeBase {
public:
    typedef std::shared_ptr<TopicTypeBase> Ptr;
    typedef std::map<PyObject*, Ptr> TopicTypes;

    virtual PyObject* get_python_class() = 0;

    virtual const char* type_name() = 0;

    virtual void register_type(PyObject* pyparticipant) = 0;

    virtual PyObject* take_next_sample(PyObject* pyreader) = 0;

    virtual PyObject* write(PyObject* pywriter, PyObject* pysample) = 0;

    static TopicTypeBase* find(PyObject* pytype)
    {
        Global* global = &Singleton<Global>::getInstance();

        TopicTypes::iterator i = global->topic_types_().find(pytype);
        if (i == global->topic_types_().end()) {
            throw Exception("Not a Valid PyOpenDDS Type", PyExc_TypeError);
        }
        return i->second.get();
    }
};

template<typename T>
class TopicType: public TopicTypeBase {
public:
    typedef typename OpenDDS::DCPS::DDSTraits<T> Traits;

    typedef T IdlType;
    typedef typename Traits::MessageSequenceType IdlTypeSequence;

    typedef typename Traits::TypeSupportType TypeSupport;
    typedef typename Traits::TypeSupportImplType TypeSupportImpl;
    typedef typename Traits::DataWriterType DataWriter;
    typedef typename Traits::DataReaderType DataReader;

    static void init()
    {
        Global* global = &Singleton<Global>::getInstance();

        Ptr type{ new TopicType<IdlType> };
        global->topic_types_().insert(TopicTypes::value_type(Type<IdlType>::get_python_class(), type));
    }

    PyObject* get_python_class()
    {
        return Type<IdlType>::get_python_class();
    }

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
            DDS::TypeSupport_var ts = static_cast<TypeSupport*>(PyCapsule_GetPointer(capsule, nullptr));
            if (ts) ts = nullptr;
        }
    }

    void register_type(PyObject* pyparticipant)
    {
        // Get DomainParticipant_var
        DDS::DomainParticipant* participant =
        get_capsule<DDS::DomainParticipant>(pyparticipant);
        if (!participant) {
            throw Exception("Could not get native participant", PyExc_TypeError);
        }

        // Register with OpenDDS
        TypeSupportImpl* type_support = new TypeSupportImpl;
        if (type_support->register_type(participant, "") != DDS::RETCODE_OK) {
            delete type_support;
            type_support = nullptr;
            throw Exception("Could not create register type", Errors::PyOpenDDS_Error());
        }

        // Store TypeSupport in Python Participant
        Ref capsule = PyCapsule_New(type_support, nullptr, delete_typesupport);
        if (!capsule) throw Exception();

        Ref list { PyObject_GetAttrString(pyparticipant, "_registered_typesupport") };
        if (!list || PyList_Append(*list, *capsule))
            throw Exception();
    }

    /**
    * Callback for Python to call when the sample capsule is deleted
    */
    static void delete_sample(PyObject* capsule)
    {
        printf("delete_sample\n");
        if (PyCapsule_CheckExact(capsule)) {
            IdlType* sample = static_cast<IdlType*>(PyCapsule_GetPointer(capsule, nullptr));
            if (sample) delete sample;
        }
    }

    PyObject* take_next_sample(PyObject* pyreader)
    {
        DDS::DataReader* reader = get_capsule<DDS::DataReader>(pyreader);
        if (!reader) throw Exception();

        DataReader* reader_impl = DataReader::_narrow(reader);
        if (!reader_impl) {
            throw Exception("Could not narrow reader implementation", Errors::PyOpenDDS_Error());
        }

// #ifndef __APPLE__
//         // TODO: wait causes segmentation fault
//         DDS::ReadCondition_var read_condition = reader_impl->create_readcondition(
//             DDS::ANY_SAMPLE_STATE, DDS::ANY_VIEW_STATE, DDS::ANY_SAMPLE_STATE);
//         DDS::WaitSet_var ws = new DDS::WaitSet;
//         ws->attach_condition(read_condition);

//         DDS::ConditionSeq active;
//         const DDS::Duration_t max_wait_time = {60, 0};

//         if (Errors::check_rc(ws->wait(active, max_wait_time))) {
//             throw Exception();
//         }
//         ws->detach_condition(read_condition);
//         reader_impl->delete_readcondition(read_condition);

//         IdlType sample;
//         DDS::SampleInfo info;
//         if (Errors::check_rc(reader_impl->take_next_sample(sample, info))) {
//             throw Exception();
//         }
// #else
        // TODO: fallback to naive implementation
        
        IdlType* sample = new IdlType();
        DDS::SampleInfo info;
        DDS::ReturnCode_t rc = reader_impl->take_next_sample(*sample, info);
        if (rc != DDS::RETCODE_OK) {
            // TODO: Temporarily inhibit this error and let the user check for its return code
            throw Exception("reader_impl->take_next_sample() failed", Errors::PyOpenDDS_Error());
            Py_RETURN_NONE;
        }
// #endif
        if (info.valid_data) {
            PyObject* rv = nullptr;
            Type<IdlType>::cpp_to_python(*sample, rv);
            set_capsule(rv, sample, delete_sample);
            return rv;
        } else {
            throw Exception("received invalid data", Errors::PyOpenDDS_Error());
            Py_RETURN_NONE;
        }
    }

    PyObject* write(PyObject* pywriter, PyObject* pysample)
    {
        DDS::DataWriter* writer = get_capsule<DDS::DataWriter>(pywriter);
        if (!writer) throw Exception();

        DataWriter* writer_impl = DataWriter::_narrow(writer);
        if (!writer_impl) {
            throw Exception("Could not narrow writer implementation", Errors::PyOpenDDS_Error());
        }

        IdlType rv;
        Type<IdlType>::python_to_cpp(pysample, rv);

        DDS::ReturnCode_t rc = writer_impl->write(rv, DDS::HANDLE_NIL);
        if (rc != DDS::RETCODE_OK) {
            // TODO: Temporarily inhibit this exception and let the user check for its return code
            // throw Exception("Writer could not write sample", Errors::PyOpenDDS_Error());
        }
        //  if (Errors::check_rc(rc)) return nullptr;

        return PyLong_FromLong(rc);
    }
};

} // namesapce pyopendds

#endif // PYOPENDDS_TOPICTYPE_HEADER
