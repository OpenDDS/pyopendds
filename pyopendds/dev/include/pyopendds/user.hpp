#ifndef PYOPENDDS_USER_HEADER
#define PYOPENDDS_USER_HEADER

#include "common.hpp"

#include <dds/DCPS/TypeSupportImpl.h>
#include <dds/DdsDcpsDomainC.h>
#include <dds/DCPS/WaitSet.h>

#include <stdexcept>
#include <map>
#include <memory>
#include <limits>

namespace pyopendds {

template<typename T>
class Type /*{
public:
  static PyObject* get_python_class();
  static void cpp_to_python(const T& cpp, PyObject*& py);
  static void python_to_cpp(PyObject* py, T& cpp);
}*/;

template<typename T>
class IntegerType {
public:
  typedef std::numeric_limits<T> limits;
  typedef std::conditional<limits::is_signed, long, unsigned long> LongType;

  static PyObject* get_python_class()
  {
    return dynamic_cast<PyObject*>(&PyLong_Type);
  }

  static void cpp_to_python(const T& cpp, PyObject*& py)
  {
    if (limits::is_signed) {
      py = PyLong_FromLong(cpp);
    } else {
      py = PyLong_FromUnsignedLong(cpp);
    }
    if (!py) throw Exception();
  }

  static void python_to_cpp(PyObject* py, T& cpp)
  {
    LongType value;
    if (limits::is_signed) {
      value = PyLong_AsLong(py);
    } else {
      value = PyLong_AsUnsignedLong(py);
    }
    if (value < limits::min() || value > limits::max()) {
      throw Exception(
        "Integer Value is Out of Range for IDL Type", PyExc_ValueError);
    }
    if (value == -1 && PyErr_Occurred()) throw Exception();
    cpp = value;
  }
};

typedef ::CORBA::Long i32;
template<> class Type<i32>: public IntegerType<i32> {};

// TODO: Put Other Integer Types Here

const char* string_data(const std::string& cpp)
{
  return cpp.data();
}

const char* string_data(const char* cpp)
{
  return cpp;
}

size_t string_length(const std::string& cpp)
{
  return cpp.size();
}

size_t string_length(const char* cpp)
{
  return std::strlen(cpp);
}

template<typename T>
class StringType {
public:
  static PyObject* get_python_class()
  {
    return dynamic_cast<PyObject*>(&PyUnicode_Type);
  }

  static void cpp_to_python(const T& cpp, PyObject*& py, const char* encoding)
  {
    PyObject* o = PyUnicode_Decode(
      string_data(cpp), string_length(cpp), encoding, "strict");
    if (!o) throw Exception();
    py = o;
  }

  static void python_to_cpp(PyObject* py, T& cpp)
  {
    // TODO: Encode or Throw Unicode Error
  }
};

// TODO: Add seperate RawStringType where get_python_class returns PyBytes_Type

typedef
#ifdef CPP11_IDL
  std::string
#else
  ::TAO::String_Manager
#endif
  s8;
template<> class Type<s8>: public StringType<s8> {};
// TODO: Put Other String/Char Types Here

// TODO: FloatingType for floating point type

class TopicTypeBase {
public:
  virtual PyObject* get_python_class() = 0;
  virtual const char* type_name() = 0;
  virtual void register_type(PyObject* pyparticipant) = 0;
  virtual PyObject* take_next_sample(PyObject* pyreader) = 0;

  typedef std::shared_ptr<TopicTypeBase> Ptr;
  typedef std::map<PyObject*, Ptr> TopicTypes;

  static TopicTypeBase* find(PyObject* pytype)
  {
    TopicTypes::iterator i = topic_types_.find(pytype);
    if (i == topic_types_.end()) {
      throw Exception("Not a Valid PyOpenDDS Type", PyExc_TypeError);
    }
    return i->second.get();
  }

private:
  static TopicTypes topic_types_;
};

template<typename T>
class TopicType : public TopicTypeBase {
public:
  typedef typename OpenDDS::DCPS::DDSTraits<T> Traits;

  typedef T IdlType;
  typedef typename Traits::MessageSequenceType IdlTypeSequence;

  typedef typename Traits::TypeSupportType TypeSupport;
  typedef typename Traits::TypeSupportTypeImpl TypeSupportImpl;
  typedef typename Traits::DataWriterType DataWriter;
  typedef typename Traits::DataReaderType DataReader;

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
      delete static_cast<TypeSupportImpl*>(
        PyCapsule_GetPointer(capsule, nullptr));
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
      type_support = 0;
      throw Exception(
        "Could not create register type", Errors::PyOpenDDS_Error());
    }

    // Store TypeSupport in Python Participant
    Ref capsule = PyCapsule_New(
      type_support, nullptr, delete_typesupport);
    if (!capsule) throw Exception();
    Ref list{PyObject_GetAttrString(pyparticipant, "_registered_typesupport")};
    if (!list || PyList_Append(*list, *capsule)) throw Exception();
  }

  PyObject* take_next_sample(PyObject* pyreader)
  {
    DDS::DataReader* reader = get_capsule<DDS::DataReader>(pyreader);
    if (!reader) throw Exception();

    DataReader* reader_impl = DataReader::_narrow(reader);
    if (!reader_impl) {
      throw Exception(
        "Could not narrow reader implementation", Errors::PyOpenDDS_Error());
    }

    DDS::ReadCondition_var read_condition = reader_impl->create_readcondition(
      DDS::ANY_SAMPLE_STATE, DDS::ANY_VIEW_STATE, DDS::ANY_SAMPLE_STATE);
    DDS::WaitSet_var ws = new DDS::WaitSet;
    ws->attach_condition(read_condition);
    DDS::ConditionSeq active;
    const DDS::Duration_t max_wait_time = {10, 0};
    if (Errors::check_rc(ws->wait(active, max_wait_time))) {
      throw Exception();
    }
    ws->detach_condition(read_condition);
    reader_impl->delete_readcondition(read_condition);

    IdlType sample;
    DDS::SampleInfo info;
    if (Errors::check_rc(reader_impl->take_next_sample(sample, info))) {
      throw Exception();
    }

    PyObject* rv = nullptr;
    Type<IdlType>::cpp_to_python(sample, rv);

    return rv;
  }

  PyObject* get_python_class()
  {
    return Type<IdlType>::get_python_class();
  }

  static void init()
  {
    Ptr type{new TopicType<IdlType>};
    topic_types_.insert(TopicTypes::value_type(Type<IdlType>::get_python_class(), type));
  }
};

} // namespace pyopendds

#endif
