cmake_minimum_required(VERSION 3.12)
project({{ native_package_name }})

find_package(Python3 COMPONENTS Development REQUIRED)
find_package(OpenDDS REQUIRED)
find_package({{ idl_library_cmake_name }} REQUIRED)

add_library({{ native_package_name }} SHARED {{ native_package_name }}.cpp)
target_link_libraries({{ native_package_name }} PRIVATE Python3::Python)
target_link_libraries({{ native_package_name }} PRIVATE {{ idl_library_cmake_name }})

# Set filename to exactly what Python is expecting
set_target_properties({{ native_package_name }} PROPERTIES
  PREFIX ""
  LIBRARY_OUTPUT_NAME ${PYOPENDDS_NATIVE_FILENAME}
  SUFFIX ""
)
