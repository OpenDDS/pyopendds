from jinja2 import PackageLoader


def gen_cmakelist(target_name: str,
                  pyopendds_ldir: str,
                  idl_files: list,
                  include_dirs: list,
                  venv_path: str = ""):
    from jinja2 import Environment, FileSystemLoader
    file_loader = PackageLoader(package_name='pyopendds.dev.pyidl',
                                package_path='templates')
    env = Environment(loader=file_loader)

    cmakelist = env.get_template('cmakefile.tpl')

    context = {
        'target_name': target_name,
        'idl_list': idl_files,
        'include_path': include_dirs,
    }

    output = cmakelist.render(context)
    return output

def gen_cmakeconfig(target_name: str,
                  pyopendds_ldir: str,
                  idl_files: list,
                  include_dirs: list,
                  venv_path: str = ""):
    from jinja2 import Environment, FileSystemLoader
    file_loader = PackageLoader(package_name='pyopendds.dev.pyidl',
                                package_path='templates')
    env = Environment(loader=file_loader)

    cmake_config = env.get_template('Config.in.tpl')

    context = {
        'target_name': target_name,
        'idl_list': idl_files,
        'include_path': include_dirs,
    }

    output = cmake_config.render(context)
    return output
