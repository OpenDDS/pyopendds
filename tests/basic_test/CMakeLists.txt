cmake_minimum_required(VERSION 3.10)

project(PyOpenDDS_Test)

list(APPEND CMAKE_MODULE_PATH "$ENV{DDS_ROOT}/cmake")
find_package(OpenDDS)

add_executable(publisher publisher.cpp)
add_library(basic_idl SHARED)
OPENDDS_TARGET_SOURCES(basic_idl PUBLIC basic.idl OPENDDS_IDL_OPTIONS -Gitl)
target_link_libraries(publisher OpenDDS::OpenDDS)
target_link_libraries(publisher basic_idl)
