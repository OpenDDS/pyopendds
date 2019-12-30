cmake_minimum_required(VERSION 3.10)

project(PyOpenDDS_Test)

list(APPEND CMAKE_MODULE_PATH "$ENV{DDS_ROOT}/cmake")
find_package(OpenDDS REQUIRED)

add_library(basic_idl SHARED)
OPENDDS_TARGET_SOURCES(basic_idl PUBLIC basic.idl OPENDDS_IDL_OPTIONS -Gitl)
export(
  TARGETS basic_idl
  FILE "${CMAKE_CURRENT_BINARY_DIR}/basic_idlConfig.cmake"
)

add_executable(publisher publisher.cpp)
target_link_libraries(publisher OpenDDS::OpenDDS)
target_link_libraries(publisher basic_idl)
