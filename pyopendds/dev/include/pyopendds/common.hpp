#ifndef PYOPENDDS_COMMON_HEADER
#define PYOPENDDS_COMMON_HEADER

// Python.h should always be first
#define PY_SSIZE_T_CLEAN
#ifdef _DEBUG
#  undef _DEBUG
#  define PYOPENDDS_DEBUG
#endif
#include <Python.h>
#ifdef PYOPENDDS_DEBUG
#  undef PYOPENDDS_DEBUG
#  define _DEBUG
#endif

#include <dds/DdsDcpsInfrastructureC.h>

namespace pyopendds {

class Exception : public std::exception {
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
  {
  }

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

/**
 * Simple Manager For PyObjects that are to be decremented when the instance is
 * deleted.
 */
class Ref {
public:
  Ref(PyObject* o = nullptr)
    : o_(o)
  {
  }
  ~Ref() { Py_XDECREF(o_); }
  PyObject*& operator*() { return o_; }
  Ref& operator=(PyObject* o)
  {
    Py_XDECREF(o_);
    o_ = o;
    return *this;
  }
  operator bool() const { return o_; }
  void operator++(int) { Py_INCREF(o_); }

private:
  PyObject* o_;
};

/// Name of PyCapule Attribute Holding the C++ Object
const char* capsule_name = "_cpp_object";

/**
 * Get Contents of Capsule from a PyObject
 */
template <typename T>
T* get_capsule(PyObject* obj)
{
  T* rv = nullptr;
  PyObject* capsule = PyObject_GetAttrString(obj, capsule_name); // nr
  if (capsule) {
    if (PyCapsule_IsValid(capsule, nullptr)) {
      rv = static_cast<T*>(PyCapsule_GetPointer(capsule, nullptr));
    }
    Py_DECREF(capsule);
  } else {
    PyErr_Clear();
  }
  if (!rv) {
    PyErr_SetString(PyExc_TypeError, "Python object does not have a valid capsule pointer");
  }
  return rv;
}

template <typename T>
bool set_capsule(PyObject* py, T* cpp, PyCapsule_Destructor cb)
{
  PyObject* capsule = PyCapsule_New(cpp, nullptr, cb);
  if (!capsule) {
    return true;
  }
  const bool error = PyObject_SetAttrString(py, capsule_name, capsule);
  Py_DECREF(capsule);
  return error;
}

class Errors {
public:
  static PyObject* pyopendds() { return pyopendds_; }

  static PyObject* PyOpenDDS_Error() { return PyOpenDDS_Error_; }

  static PyObject* ReturnCodeError() { return ReturnCodeError_; }

  static bool cache()
  {
    pyopendds_ = PyImport_ImportModule("pyopendds");
    if (!pyopendds_) {
      return true;
    }

    PyOpenDDS_Error_ = PyObject_GetAttrString(pyopendds_, "PyOpenDDS_Error");
    if (!PyOpenDDS_Error_) {
      return true;
    }

    ReturnCodeError_ = PyObject_GetAttrString(pyopendds_, "ReturnCodeError");
    if (!ReturnCodeError_) {
      return true;
    }

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

} // namespace pyopendds

#endif
