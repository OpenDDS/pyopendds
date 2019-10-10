# CMakeLists for Native Part of PyOpenDDS
cmake_minimum_required(VERSION 3.12)
project(PyOpenDDS)

# TODO: HARDCODED IDL
set(HARDCODED_IDL libreading.so)

# Find Python
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Find OpenDDS
list(APPEND CMAKE_MODULE_PATH "$ENV{DDS_ROOT}/cmake")
find_package(OpenDDS REQUIRED)

# Define _pyopendds
add_library(_pyopendds SHARED _pyopendds.cpp)

# Set filename to exactly what Python is expecting
set_target_properties(_pyopendds PROPERTIES
  PREFIX ""
  LIBRARY_OUTPUT_NAME ${PYOPENDDS_NATIVE_FILENAME}
  SUFFIX ""
)

# Connect to OpenDDS
OPENDDS_TARGET_SOURCES(_pyopendds PUBLIC)
target_link_libraries(_pyopendds OpenDDS::OpenDDS)

# Connect to Python
target_link_libraries(_pyopendds ${Python3_LIBRARIES})
target_include_directories(_pyopendds PUBLIC ${Python3_INCLUDE_DIRS})

# TODO: HARDCODED IDL
# Hardcoded Reading IDL Library
add_library(reading SHARED IMPORTED)
set_property(TARGET reading PROPERTY IMPORTED_LOCATION ${CMAKE_CURRENT_LIST_DIR}/test/build/${HARDCODED_IDL})
link_directories(test/build)
target_link_libraries(_pyopendds reading)
target_include_directories(_pyopendds PUBLIC ${CMAKE_CURRENT_LIST_DIR}/test/build)
