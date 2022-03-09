cmake_minimum_required(VERSION 3.12)
project(PyOpenDDS_Test CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenDDS REQUIRED)

add_library(basic_idl SHARED)
if(${CPP11_IDL})
    set(opendds_idl_mapping_option "-Lc++11")
endif()
OPENDDS_TARGET_SOURCES(basic_idl "basic.idl"
    OPENDDS_IDL_OPTIONS "-Gitl" "${opendds_idl_mapping_option}")
target_link_libraries(basic_idl PUBLIC OpenDDS::Dcps)
export(
    TARGETS basic_idl
    FILE "${CMAKE_CURRENT_BINARY_DIR}/basic_idlConfig.cmake"
)

# add_library(airbus_idl SHARED)
# if(${CPP11_IDL})
#     set(opendds_idl_mapping_option "-Lc++11")
# endif()
# OPENDDS_TARGET_SOURCES(airbus_idl "airbusdds.idl"
#     OPENDDS_IDL_OPTIONS "-Gitl" "${opendds_idl_mapping_option}")
# target_link_libraries(airbus_idl PUBLIC OpenDDS::Dcps)
# export(
#     TARGETS airbus_idl
#     FILE "${CMAKE_CURRENT_BINARY_DIR}/airbus_idlConfig.cmake"
# )

add_executable(publisher publisher.cpp)
target_link_libraries(publisher OpenDDS::OpenDDS basic_idl)
if(${CPP11_IDL})
    set_target_properties(publisher PROPERTIES
        COMPILE_DEFINITIONS "CPP11_IDL")
endif()

add_executable(subscriber subscriber.cpp DataReaderListenerImpl.cpp)
target_link_libraries(subscriber OpenDDS::OpenDDS basic_idl)
if(${CPP11_IDL})
    set_target_properties(subscriber PROPERTIES
        COMPILE_DEFINITIONS "CPP11_IDL")
endif()
