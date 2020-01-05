# CMakeLists for Native Part of PyOpenDDS
cmake_minimum_required(VERSION 3.12)
project(PyOpenDDS)

# Find Python
find_package(Python3 COMPONENTS Development REQUIRED)

# Find OpenDDS
list(APPEND CMAKE_MODULE_PATH "$ENV{DDS_ROOT}/cmake")
find_package(OpenDDS REQUIRED)

# Define _pyopendds
add_library(_pyopendds SHARED _pyopendds.cpp)
target_link_libraries(_pyopendds OpenDDS::Dcps)
target_link_libraries(_pyopendds Python3::Python)

# Set filename to exactly what Python is expecting
set_target_properties(_pyopendds PROPERTIES
  PREFIX ""
  LIBRARY_OUTPUT_NAME ${PYOPENDDS_NATIVE_FILENAME}
  SUFFIX ""
)
