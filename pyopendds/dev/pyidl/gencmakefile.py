
def gen_cmakelist(target_name: str,
                  pyopendds_ldir: str,
                  idl_files: list,
                  include_dirs: list,
                  venv_path: str = ""):
    statement_0 = ""
    for idx, include_dir in enumerate(include_dirs):
        statement_0 += f'set(inc_dir_{idx} "{include_dir}")\n'

    statement_1 = ""
    for idx, _ in enumerate(include_dirs):
        statement_1 += f'\ntarget_include_directories({target_name}_idl PUBLIC "${{inc_dir_{idx}}}")'

    statement_3 = ""
    for idl_file in idl_files:
        statement_3 += f'\n    {idl_file}'

    statement_4 = ""
    for idx, _ in enumerate(include_dirs):
        statement_4 += f'\n    -I${{inc_dir_{idx}}}'

    statement_5 = ""
    if venv_path:
        statement_5 += f'set_target_properties({target_name}_idl PROPERTIES\n'
        statement_5 += f'    LIBRARY_OUTPUT_DIRECTORY "{venv_path}/lib/pyidl/{target_name}"\n'
        statement_5 += ')'

    return f"""
cmake_minimum_required(VERSION 3.10)

project({target_name})

list(APPEND CMAKE_MODULE_PATH "$ENV{{DDS_ROOT}}/cmake")
find_package(OpenDDS REQUIRED)
{statement_0}
add_library({target_name}_idl SHARED)
target_include_directories({target_name}_idl PUBLIC "${{CMAKE_CURRENT_SOURCE_DIR}}/build"){statement_1}
{statement_5}

if(${{CPP11_IDL}})
    set(opendds_idl_mapping_option "-Lc++11")
endif()

set(OPENDDS_FILENAME_ONLY_INCLUDES ON)
OPENDDS_TARGET_SOURCES({target_name}_idl PUBLIC{statement_3}
    OPENDDS_IDL_OPTIONS "-Gitl" "${{opendds_idl_mapping_option}}"{statement_4}
)

target_link_libraries({target_name}_idl PUBLIC OpenDDS::Dcps)
export(
    TARGETS {target_name}_idl
    FILE "${{CMAKE_CURRENT_BINARY_DIR}}/{target_name}_idlConfig.cmake"
)

target_include_directories({target_name}_idl PUBLIC
    "{pyopendds_ldir}"
)

"""
