#ifndef PYOPENDDS_BASICTYPE_HEADER
#define PYOPENDDS_BASICTYPE_HEADER

#include <Python.h>

#include <dds/DCPS/TypeSupportImpl.h>

#include <limits>
#include <stdexcept>
#include <string>

namespace pyopendds {

template<typename T>
class Type;

template<typename T>
class BooleanType {
public:
    static PyObject* get_python_class()
    {
        return Py_False;
    }

    static void cpp_to_python(const T& cpp, PyObject*& py)
    {
        py = PyBool_FromLong(cpp);
    }

    static void python_to_cpp(PyObject* py, T& cpp)
    {
        // PyBool_Check always return true
        //if (PyBool_Check(py)) throw Exception("Not a boolean", PyExc_ValueError);

        if (py == Py_True) {
            cpp = true;
        } else {
            cpp = false;
        }
    }
};


PyObject* pyopendds_mod_str = NULL;
PyObject* pyopendds_mod = NULL;

template<typename T>
class IntegerType {
public:
    typedef std::numeric_limits<T> limits;
//    typedef std::conditional<limits::is_signed, long, unsigned long> LongType;

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
    }

    static void python_to_cpp(PyObject* py, T& cpp)
    {
        T value;
        if (limits::is_signed) {
            if (sizeof(T) == sizeof(long long)) {
                value = PyLong_AsLongLong(py);
            } else {
                    value = PyLong_AsLong(py);
            }
        } else {
            if (sizeof(T) == sizeof(long long)) {
                value = PyLong_AsUnsignedLongLong(py);
            } else {
                    value = PyLong_AsUnsignedLong(py);
            }
        }
        if (value < limits::lowest() || value > limits::max()) {
            throw Exception("Integer Value is Out of Range for IDL Type", PyExc_ValueError);
        }
        if (value == -1 && PyErr_Occurred())
            throw Exception();

        cpp = T(value);
    }

private:
    static bool initPyopenddsModule()
    {
        // Creating python string for module
        if (!pyopendds_mod_str) {
            pyopendds_mod_str = PyUnicode_FromString((char*) "pyopendds.util");
            if (!pyopendds_mod_str)
                throw Exception("Cannot create Python string \"pyopendds.util\"", PyExc_NameError);
        }

        // Importing pyopendds.util module
        if (!pyopendds_mod) {
            pyopendds_mod = PyImport_Import(pyopendds_mod_str);
            if (!pyopendds_mod)
                throw Exception("Cannot import \"pyopendds.util\"", PyExc_ImportError);
        }

        return true;
    }
};

template<typename T>
class FloatingType {
public:
    typedef std::numeric_limits<T> limits;

    static PyObject* get_python_class()
    {
        return PyFloat_FromDouble(0.0);
    }

    static void cpp_to_python(const T& cpp, PyObject*& py)
    {
        py = PyFloat_FromDouble((double)cpp);
    }

    static void python_to_cpp(PyObject* py, T& cpp)
    {
        double value;
        value = PyFloat_AsDouble(py);
        if (value < limits::lowest() || value > limits::max()) {
            throw Exception("Floating Value is Out of Range for IDL Type", PyExc_ValueError);
        }

        if (value == -1 && PyErr_Occurred()) throw Exception();
        cpp = value;
    }
};

const char* string_data(const std::string& cpp) { return cpp.data(); }

const char* string_data(const char* cpp) { return cpp; }

size_t string_length(const std::string& cpp) { return cpp.size(); }

size_t string_length(const char* cpp) { return std::strlen(cpp); }

template<typename T>
class StringType {
public:
    static PyObject* get_python_class()
    {
        // TODO: Add seperate RawStringType where get_python_class returns PyBytes_Type
        return PyUnicode_FromString("");
    }

    static void cpp_to_python(const T& cpp, PyObject*& py, const char* encoding)
    {
        PyObject* o = PyUnicode_Decode(string_data(cpp), string_length(cpp), encoding, "strict");
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

typedef ::CORBA::Boolean b;
template<> class Type<b>: public BooleanType<b> {};

typedef ::CORBA::LongLong i64;
template<> class Type<i64>: public IntegerType<i64> {};

typedef ::CORBA::ULongLong u64;
template<> class Type<u64>: public IntegerType<u64> {};

typedef ::CORBA::Long i32;
template<> class Type<i32>: public IntegerType<i32> {};

typedef ::CORBA::ULong u32;
template<> class Type<u32>: public IntegerType<u32> {};

typedef ::CORBA::Short i16;
template<> class Type<i16>: public IntegerType<i16> {};

typedef ::CORBA::UShort u16;
template<> class Type<u16>: public IntegerType<u16> {};

typedef ::CORBA::Char c8;
template<> class Type<c8>: public IntegerType<c8> {};

typedef ::CORBA::WChar c16;
template<> class Type<c16>: public IntegerType<c16> {};

typedef ::CORBA::Octet u8;
template<> class Type<u8>: public IntegerType<u8> {};

typedef ::CORBA::Float f32;
template<> class Type<f32>: public FloatingType<f32> {};

typedef ::CORBA::Double f64;
template<> class Type<f64>: public FloatingType<f64> {};

typedef
#ifdef CPP11_IDL
std::string
#else
::TAO::String_Manager
#endif
s8;
template<> class Type<s8>: public StringType<s8> {};
// TODO: Put Other String/Char Types Here

} // namesapce pyopendds

#endif // PYOPENDDS_BASICTYPE_HEADER
