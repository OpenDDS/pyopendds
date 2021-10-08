cmake_minimum_required(VERSION 3.12)
project(pyopendds_itl2py_test CXX)

find_package(OpenDDS REQUIRED)

add_library(itl2py_test_idl SHARED)
OPENDDS_TARGET_SOURCES(itl2py_test_idl itl2py_test.idl another_file.idl OPENDDS_IDL_OPTIONS -Gitl)
target_link_libraries(itl2py_test_idl PUBLIC OpenDDS::Dcps)
export(
  TARGETS itl2py_test_idl
  FILE "${CMAKE_CURRENT_BINARY_DIR}/itl2py_test_idlConfig.cmake"
)
