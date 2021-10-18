# CMakeLists for Native Part of PyOpenDDS
cmake_minimum_required(VERSION 3.12)
project(PyOpenDDS CXX)

# Find Python
find_package(Python3 ${PYOPENDDS_PYTHON_VERSION} EXACT
  COMPONENTS Development
  REQUIRED
)

# Find OpenDDS
list(APPEND CMAKE_MODULE_PATH "$ENV{DDS_ROOT}/cmake")
find_package(OpenDDS REQUIRED)

# Define _pyopendds
Python3_add_library(_pyopendds MODULE _pyopendds.cpp)
set_target_properties(_pyopendds PROPERTIES SUFFIX ${PYOPENDDS_NATIVE_EXT_SUFFIX})
set_property(TARGET _pyopendds PROPERTY CXX_STANDARD 14)
set_property(TARGET _pyopendds PROPERTY CXX_STANDARD_REQUIRED ON)
target_include_directories(_pyopendds PRIVATE ${PYOPENDDS_INCLUDE})
target_link_libraries(_pyopendds PUBLIC OpenDDS::Dcps)
