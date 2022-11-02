project( {{ target_name }} CXX)
cmake_minimum_required(VERSION 3.3)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

set(INSTALL_IMPORTED_RUNTIME_ARTIFACTS TRUE)
if(${CMAKE_VERSION} VERSION_LESS "3.21.0" OR OPENDDS_STATIC)
  set(INSTALL_IMPORTED_RUNTIME_ARTIFACTS FALSE)
endif()

set(PROJECT_NAME {{ target_name }}_idl)

find_package(OpenDDS REQUIRED)

if(NOT DEFINED INSTALL_IMPORTED_RUNTIME_ARTIFACTS)
  set(INSTALL_IMPORTED_RUNTIME_ARTIFACTS TRUE)
  if(${CMAKE_VERSION} VERSION_LESS "3.21.0" OR OPENDDS_STATIC)
    set(INSTALL_IMPORTED_RUNTIME_ARTIFACTS FALSE)
  endif()
endif()

add_library(${PROJECT_NAME} ${OPENDDS_LIBRARY_TYPE})
target_include_directories(${PROJECT_NAME}
  PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
    "$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>"
)

set(opendds_libs OpenDDS::Dcps)
target_link_libraries(${PROJECT_NAME} PUBLIC ${opendds_libs})
OPENDDS_TARGET_SOURCES(${PROJECT_NAME}
  PUBLIC
  {% for idl in idl_list %} {{ idl }} {% endfor %}
  OPENDDS_IDL_OPTIONS "-Gitl" {% for path in include_path %} -I "{{ path }}" {% endfor %}
  TAO_IDL_OPTIONS {% for path in include_path %} -I "{{ path }}" {% endfor %}
  ALWAYS_GENERATE_LIB_EXPORT_HEADER TRUE
)

set(exec_perms
  OWNER_READ OWNER_WRITE OWNER_EXECUTE
  GROUP_READ GROUP_WRITE GROUP_EXECUTE
  WORLD_READ WORLD_EXECUTE)

set(targets "${PROJECT_NAME}Targets")
install(TARGETS ${PROJECT_NAME}
  EXPORT ${targets}
  LIBRARY
    DESTINATION lib
    PERMISSIONS ${exec_perms}
  RUNTIME
    DESTINATION lib
    PERMISSIONS ${exec_perms}
  ARCHIVE DESTINATION lib
)
install(DIRECTORY "include/" DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
  FILES_MATCHING PATTERN "*.h")
get_target_property(generated_files ${PROJECT_NAME} OPENDDS_ALL_GENERATED_INTERFACE_FILES)
get_target_property(generated_directory ${PROJECT_NAME} OPENDDS_GENERATED_DIRECTORY)
foreach(file ${generated_files})
  file(RELATIVE_PATH dest ${generated_directory} ${file})
  string(REGEX REPLACE "^include/" "" dest ${dest})
  get_filename_component(dest ${dest} DIRECTORY)
  install(FILES ${file} DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/${dest}")
endforeach()
set(cmake_dest "${CMAKE_INSTALL_DATAROOTDIR}/cmake/${PROJECT_NAME}")
install(EXPORT ${targets}
  FILE "${targets}.cmake"
  NAMESPACE "${PROJECT_NAME}::"
  DESTINATION ${cmake_dest}
)
set(config_cmake "${PROJECT_NAME}Config.cmake")
set(build_config_cmake "${CMAKE_CURRENT_BINARY_DIR}/${config_cmake}")
configure_package_config_file(
  "${config_cmake}.in" ${build_config_cmake}
  INSTALL_DESTINATION ${cmake_dest}
)
install(FILES ${build_config_cmake} DESTINATION ${cmake_dest})

if(INSTALL_IMPORTED_RUNTIME_ARTIFACTS)
  opendds_get_library_dependencies(opendds_dep_libs ${opendds_libs})
  install(IMPORTED_RUNTIME_ARTIFACTS
    ${opendds_dep_libs}
    LIBRARY
      DESTINATION lib
      PERMISSIONS ${exec_perms}
    RUNTIME
      DESTINATION lib
      PERMISSIONS ${exec_perms}
  )
endif()
