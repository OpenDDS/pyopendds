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
class BooleanType {
public:
  static PyObject* get_python_class()
  {
    return Py_False;
  }

  static void cpp_to_python(const T& cpp, PyObject*& py)
  {
    if ( ! cpp ) {
       py = Py_False;
     } else {
       py = Py_True;
     }
  }

  static void python_to_cpp(PyObject* py, T& cpp)
  {
    if (PyBool_Check(py)) {
      throw Exception("Not a boolean", PyExc_ValueError);
    }
    if(py) {
        cpp = true;
    } else {
        cpp = false;
    }
  }
};

//typedef ::CORBA::Boolean bool;
template<> class Type<bool>: public BooleanType<bool> {};

template<typename T>
class IntegerType {
public:
  typedef std::numeric_limits<T> limits;
  typedef std::conditional<limits::is_signed, long, unsigned long> LongType;

  static PyObject* get_python_class()
  {
    return PyLong_FromLong(0);
  }

  static void cpp_to_python(const T& cpp, PyObject*& py)
  {
    if (limits::is_signed) {
        if (sizeof(cpp) > sizeof(long)) {
            py = PyLong_FromLongLong(cpp);
        } else {
            py = PyLong_FromLong(cpp);
        }
    } else {
        if (sizeof(cpp) > sizeof(long)) {
            py = PyLong_FromUnsignedLongLong(cpp);
        } else {
            py = PyLong_FromUnsignedLong(cpp);
        }
    }
    if (!py) throw Exception();
  }

  static void python_to_cpp(PyObject* py, T& cpp)
  {
    T value; //todo: change to LongType
    if (limits::is_signed) {
        if (sizeof(cpp) > sizeof(long)) {
            value = PyLong_AsLongLong(py);
        } else {
            value = PyLong_AsLong(py);
        }
    } else {
        if (sizeof(cpp) > sizeof(long)) {
            value = PyLong_AsUnsignedLongLong(py);
        } else {
            value = PyLong_AsUnsignedLong(py);
        }
    }
    if (value < limits::min() || value > limits::max()) {
      throw Exception(
        "Integer Value is Out of Range for IDL Type", PyExc_ValueError);
    }
    if (value == -1 && PyErr_Occurred()) throw Exception();
    cpp = T(value);
  }

};

typedef ::CORBA::LongLong i64;
template<> class Type<i64>: public IntegerType<i64> {};

typedef ::CORBA::Long i32;
typedef ::CORBA::Long u32;
template<> class Type<i32>: public IntegerType<i32> {};

typedef ::CORBA::Short i16;
template<> class Type<i16>: public IntegerType<i16> {};

typedef ::CORBA::Char c8;
typedef ::CORBA::Char u8;
template<> class Type<c8>: public IntegerType<c8> {};

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
    return PyUnicode_FromString("");
  }

  static void cpp_to_python(const T& cpp, PyObject*& py, const char* encoding)
  {
    PyObject* o = PyUnicode_Decode(
      string_data(cpp), string_length(cpp), encoding, "strict");
    if (!o) throw Exception();
    py = o;
  }

  static void python_to_cpp(PyObject* py, T& cpp, const char* encoding)
  {
    PyObject* repr = PyObject_Str(py);
    if (!repr) throw Exception();
    PyObject* str = PyUnicode_AsEncodedString(repr, encoding, NULL);
    if (!str) throw Exception();
    const char *bytes = PyBytes_AS_STRING(str);
    cpp = T(bytes);
    Py_XDECREF(repr);
    Py_XDECREF(str);
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

template<typename T>
class FloatingType {
public:
  typedef std::numeric_limits<T> limits;

  static PyObject* get_python_class()
  {
    return PyFloat_FromDouble(0);
  }

  static void cpp_to_python(const T& cpp, PyObject*& py)
  {
      py = PyFloat_FromDouble((double)cpp);
      if (!py) throw Exception();
  }

  static void python_to_cpp(PyObject* py, T& cpp)
  {
    double value;
    value = PyFloat_AsDouble(py);
    if (value < limits::min() || value > limits::max()) {
      throw Exception(
        "Floating Value is Out of Range for IDL Type", PyExc_ValueError);
    }
    if (value == -1 && PyErr_Occurred()) throw Exception();
    cpp = value;
  }
};

typedef ::CORBA::Float f32;
typedef ::CORBA::Double f64;
template<> class Type<f32>: public FloatingType<f32> {};
template<> class Type<f64>: public FloatingType<f64> {};
// TODO: FloatingType for floating point type

class TopicTypeBase {
public:
  virtual PyObject* get_python_class() = 0;
  virtual const char* type_name() = 0;
  virtual void register_type(PyObject* pyparticipant) = 0;
  virtual PyObject* take_next_sample(PyObject* pyreader) = 0;
  virtual PyObject* write(PyObject* pywriter, PyObject* pysample) = 0;

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
    const DDS::Duration_t max_wait_time = {60, 0};
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
    if (info.valid_data)
        Type<IdlType>::cpp_to_python(sample, rv);
    else
        rv = Py_None;

    return rv;
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
        throw Exception(
            "WRITE ERROR", Errors::PyOpenDDS_Error());
    }
    if (Errors::check_rc(rc)) return nullptr;

    return PyLong_FromLong(rc);
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
