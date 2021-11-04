
def gen_cmakelist(target_name: str,
                  pyopendds_ldir: str,
                  idl_files: list,
                  include_dirs: list):
    statement_0 = ""
    for idx, include_dir in enumerate(include_dirs):
        statement_0 += f'set(inc_dir_{idx} "{include_dir}")\n'

    statement_1 = ""
    for idx, _ in enumerate(include_dirs):
        statement_1 += f'target_include_directories({target_name}_idl PUBLIC "${{inc_dir_{idx}}}")\n'

    statement_3 = ""
    for idl_file in idl_files:
        statement_3 += f' {idl_file}'
    statement_3 = f'PUBLIC{statement_3}'

    statement_4 = ""
    for idx, _ in enumerate(include_dirs):
        statement_4 += f' -I${{inc_dir_{idx}}}'

    return f"""
cmake_minimum_required(VERSION 3.10)

project({target_name})

list(APPEND CMAKE_MODULE_PATH "$ENV{{DDS_ROOT}}/cmake")
find_package(OpenDDS REQUIRED)
{statement_0}
add_library({target_name}_idl SHARED)
target_include_directories({target_name}_idl PUBLIC "${{CMAKE_CURRENT_SOURCE_DIR}}/build")
{statement_1}
if(${{CPP11_IDL}})
    set(opendds_idl_mapping_option "-Lc++11")
endif()

set(OPENDDS_FILENAME_ONLY_INCLUDES ON)
OPENDDS_TARGET_SOURCES({target_name}_idl {statement_3}
    OPENDDS_IDL_OPTIONS "-Gitl" "${{opendds_idl_mapping_option}}"{statement_4}
)

target_link_libraries({target_name}_idl PUBLIC OpenDDS::Dcps)
export(
    TARGETS {target_name}_idl
    FILE "${{CMAKE_CURRENT_BINARY_DIR}}/{target_name}_idlConfig.cmake"
)

target_include_directories({target_name}_idl PUBLIC "{pyopendds_ldir}")
"""