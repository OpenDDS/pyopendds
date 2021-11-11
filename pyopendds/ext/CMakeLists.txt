# CMakeLists for Native Part of PyOpenDDS
cmake_minimum_required(VERSION 3.12)
project(_pyopendds CXX)

find_package(Python3 COMPONENTS Development REQUIRED)
find_package(OpenDDS REQUIRED)

Python3_add_library(_pyopendds MODULE _pyopendds.cpp)
set_target_properties(_pyopendds PROPERTIES OUTPUT_NAME "_pyopendds")
set_property(TARGET _pyopendds PROPERTY CXX_STANDARD 14)
set_property(TARGET _pyopendds PROPERTY CXX_STANDARD_REQUIRED ON)
target_include_directories(_pyopendds PRIVATE ${PYOPENDDS_INCLUDE})
target_link_libraries(_pyopendds PRIVATE OpenDDS::Dcps)

# Handle where to install the resulting Python package
if(CALL_FROM_SETUP_PY)
    # The CMakeExtension will set CMAKE_INSTALL_PREFIX to the root
    # of the resulting wheel archive
    set(install_prefix ${CMAKE_INSTALL_PREFIX})
else()
    # The Python package is installed directly in the folder of the
    # detected interpreter (system, user, or virtualenv)
    set(install_prefix ${Python3_SITELIB})
endif()
install(
    TARGETS _pyopendds
    COMPONENT _pyopendds
    LIBRARY DESTINATION ${install_prefix}
    ARCHIVE DESTINATION ${install_prefix}
    RUNTIME DESTINATION ${install_prefix})
