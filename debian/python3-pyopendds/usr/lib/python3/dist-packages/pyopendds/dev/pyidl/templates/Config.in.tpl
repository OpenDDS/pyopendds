include(CMakeFindDependencyMacro)
find_dependency(OpenDDS REQUIRED)
include("${CMAKE_CURRENT_LIST_DIR}/{{ target_name }}_idlTargets.cmake")