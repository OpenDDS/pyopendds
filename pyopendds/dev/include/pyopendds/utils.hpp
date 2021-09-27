#ifndef PYOPENDDS_UTILS_HEADER
#define PYOPENDDS_UTILS_HEADER

#include <Python.h>

namespace pyopendds {

    /// Name of PyCapule Attribute Holding the C++ Object
    const char* capsule_name = "_cpp_object";

    /**
    * Simple Manager For PyObjects that are to be decremented when the instance is
    * deleted.
    */
    class Ref {
    public:
        Ref(PyObject* o = nullptr)
        : object_(o)
        { }

        ~Ref()
        {
            Py_XDECREF(object_);
        }

        PyObject*& operator*()
        {
            return object_;
        }

        Ref& operator=(PyObject* o)
        {
            Py_XDECREF(object_);
            object_ = o;
            return *this;
        }

        void operator++(int /*unused*/)
        {
            Py_INCREF(object_);
        }

        operator bool() const
        {
            return object_;
        }

    private:
        PyObject* object_;
    };

    /**
    * Gets contents of Capsule from a PyObject
    */
    template <typename T>
    T* get_capsule(PyObject* obj)
    {
        T* return_value = nullptr;
        PyObject* capsule = PyObject_GetAttrString(obj, capsule_name); // nr

        if (capsule) {
            if (PyCapsule_IsValid(capsule, nullptr)) {
                return_value = static_cast<T*>(PyCapsule_GetPointer(capsule, nullptr));
            }
            Py_DECREF(capsule);
        } else {
            PyErr_Clear();
        }
        if (!return_value)
            PyErr_SetString(PyExc_TypeError, "Python object does not have a valid capsule pointer");

        return return_value;
    }

    /**
    * Sets contents of Capsule
    */
    template <typename T>
    bool set_capsule(PyObject* py, T* cpp, PyCapsule_Destructor dtor)
    {
        PyObject* capsule = PyCapsule_New(cpp, nullptr, dtor);
        if (!capsule)
            return true;

        const bool error = PyObject_SetAttrString(py, capsule_name, capsule);
        Py_DECREF(capsule);

        return error;
    }

    template<typename T>
    class Singleton
    {
    public:
        static T& getInstance();

        // so we cannot accidentally delete it via pointers
        Singleton(){};

        // no copies
        Singleton(const Singleton&) = delete;

        // no self-assignments
        Singleton& operator=(const Singleton&) = delete;
    };

    template<typename T>
    T& Singleton<T>::getInstance() {

        // Guaranteed to be destroyed. Instantiated on first use. Thread safe in C++11
        static T instance;
        return instance;
    }

} // namesapce pyopendds

#endif // PYOPENDDS_UTILS_HEADER
