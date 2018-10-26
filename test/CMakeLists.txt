cmake_minimum_required(VERSION 3.10)

project(PyOpenDDS_Test)

list(APPEND CMAKE_MODULE_PATH "$ENV{DDS_ROOT}/share/cmake/Modules")
find_package(OpenDDS)

add_executable(publisher publisher.cpp)
add_library(reading SHARED)
OPENDDS_TARGET_SOURCES(reading PUBLIC Reading.idl)
OPENDDS_TARGET_SOURCES(publisher PUBLIC)
target_link_libraries(publisher OpenDDS::OpenDDS)
target_link_libraries(publisher reading)


