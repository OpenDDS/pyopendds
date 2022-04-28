# NOTE: This CMake file should not be built on its own. It's meant to be built
# as part of the Python package.
cmake_minimum_required(VERSION 3.12)
project({{ native_package_name }} CXX)

find_package(Python3 COMPONENTS Development REQUIRED)
find_package(OpenDDS REQUIRED)
set({{ idl_library_cmake_name }}_DIR {{ idl_library_build_dir }})
find_package({{ idl_library_cmake_name }} REQUIRED)

Python3_add_library({{ native_package_name }} MODULE {{ native_package_name }}.cpp)
set_target_properties({{ native_package_name }} PROPERTIES OUTPUT_NAME {{ native_package_name }})
set_property(TARGET {{ native_package_name }} PROPERTY CXX_STANDARD 14)
set_property(TARGET {{ native_package_name }} PROPERTY CXX_STANDARD_REQUIRED ON)
target_include_directories({{ native_package_name }} PRIVATE ${PYOPENDDS_INCLUDE})
target_link_libraries({{ native_package_name }} PRIVATE {{ idl_library_cmake_name }}::{{ idl_library_cmake_name }})

get_property(idl_mappings TARGET {{ idl_library_cmake_name }}::{{ idl_library_cmake_name }}
    PROPERTY OPENDDS_LANGUAGE_MAPPINGS)
if("C++11" IN_LIST idl_mappings)
    set_target_properties({{ native_package_name }} PROPERTIES
        COMPILE_DEFINITIONS "CPP11_IDL")
endif()

# Handle where to install the resulting Python package
if(CALL_FROM_SETUP_PY)
    # The CMakeExtension will set CMAKE_INSTALL_PREFIX to the root
    # of the resulting wheel archive
    set(the_install_prefix ${CMAKE_INSTALL_PREFIX})
else()
    # The Python package is installed directly in the folder of the
    # detected interpreter (system, user, or virtualenv)
    set(the_install_prefix ${Python3_SITELIB})
endif()
install(
    TARGETS {{ native_package_name }}
    COMPONENT {{ native_package_name }}
    LIBRARY DESTINATION ${the_install_prefix}
    ARCHIVE DESTINATION ${the_install_prefix}
    RUNTIME DESTINATION ${the_install_prefix})
