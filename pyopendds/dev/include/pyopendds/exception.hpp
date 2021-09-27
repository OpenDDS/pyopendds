#ifndef PYOPENDDS_EXCEPTION_HEADER
#define PYOPENDDS_EXCEPTION_HEADER

#include <Python.h>

#include <dds/DdsDcpsInfrastructureC.h>
#include <exception>

namespace pyopendds {

class Exception: public std::exception {
public:
    Exception()
    : message_(nullptr)
    , pyexc_(nullptr)
    {
        assert(PyErr_Occurred());
    }

    Exception(const char* message, PyObject* pyexc)
    : message_(message)
    , pyexc_(pyexc)
    { }

    PyObject* set() const
    {
        if (pyexc_ && message_) {
            PyErr_SetString(pyexc_, message_);
        }
        return nullptr;
    }

    virtual const char* what() const noexcept
    {
        return message_ ? message_ : "Python Exception Occurred";
    }

private:
    const char* message_;
    PyObject* pyexc_;
};


class Errors {
public:
    static PyObject* pyopendds()
    {
        return pyopendds_;
    }

    static PyObject* PyOpenDDS_Error()
    {
        return PyOpenDDS_Error_;
    }

    static PyObject* ReturnCodeError()
    {
        return ReturnCodeError_;
    }

    static bool cache()
    {
        pyopendds_ = PyImport_ImportModule("pyopendds");
        if (!pyopendds_) return true;

        PyOpenDDS_Error_ = PyObject_GetAttrString(pyopendds_, "PyOpenDDS_Error");
        if (!PyOpenDDS_Error_) return true;

        ReturnCodeError_ = PyObject_GetAttrString(pyopendds_, "ReturnCodeError");
        if (!ReturnCodeError_) return true;

        return false;
    }

    static bool check_rc(DDS::ReturnCode_t rc)
    {
        return !PyObject_CallMethod(ReturnCodeError_, "check", "k", rc);
    }

private:
    static PyObject* pyopendds_;
    static PyObject* PyOpenDDS_Error_;
    static PyObject* ReturnCodeError_;
};

} // namesapce pyopendds

#endif // PYOPENDDS_EXCEPTION_HEADER
