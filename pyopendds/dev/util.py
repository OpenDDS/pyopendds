import sys
import os
import subprocess
from pathlib import Path


__all__ = [
    'RunCommandError',
    'run_command',
    'run_python',
    'wait_or_kill',
]


class RunCommandError(Exception):
    pass


def add_to_env_var_path_list(env, name, prepend):
    if prepend:
        env[name] = os.pathsep.join([str(Path(p).resolve()) for p in prepend]) + \
            os.pathsep + env[name]


def new_environment(add_executable_paths=[], add_library_paths=[]):
    env = dict(os.environ)
    add_to_env_var_path_list(env, 'PATH', add_executable_paths)
    add_to_env_var_path_list(env, 'LD_LIBRARY_PATH', add_library_paths)
    return env


def command_repr(command):
    return repr(' '.join([str(i) for i in command]))


def non_zero_message(command, return_code):
    return '{} returned non-zero result: {}'.format(command_repr(command), return_code)


def run_command(*command, cwd=Path(), exit_on_error=False,
        add_executable_paths=[], add_library_paths=[],
        return_popen=False):
    error = None
    try:
        popen_kwargs = dict(
            cwd=str(cwd),
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=new_environment(add_executable_paths, add_library_paths),
        )
        if return_popen:
            return subprocess.Popen(command, **popen_kwargs)
        else:
            subprocess.run(command, check=True, **popen_kwargs)
    except OSError as os_error:
        error = 'Could not run {}: {}'.format(command_repr(command), str(os_error))
        if not exit_on_error:
            raise RunCommandError(error) from os_error
    except subprocess.CalledProcessError as return_code_error:
        error = non_zero_message(command, return_code_error.returncode)
        if not exit_on_error:
            raise RunCommandError(error) from return_code_error
    if exit_on_error and error is not None:
        sys.exit('ERROR: ' + error)


def run_python(*args, **kwargs) -> None:
    return run_command(sys.executable, *args, **kwargs)


def wait_or_kill(proc, timeout):
    try:
        return_code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired as ex:
        proc.kill()
        raise RunCommandError(f'Timedout, had to kill {proc.pid} '
            + command_repr(proc.args)) from ex
    if return_code != 0:
        raise RunCommandError(non_zero_message(proc.args, return_code))
