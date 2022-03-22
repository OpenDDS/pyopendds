import sys
import os
import subprocess
from pathlib import Path
import shutil

build_type = os.environ.get("PYOPENDDS_BUILD_TYPE", "Release")


def get_include_path() -> Path:
  return Path(__file__).resolve().parent / "include"


class RunCommandError(Exception):
  pass


def _add_to_env_var_path_list(env, name, prepend):
  if prepend:
    value = env[name]
    if value and not value.startswith(os.pathsep):
      value = os.pathsep + value
    env[name] = os.pathsep.join([str(Path(p).resolve()) for p in prepend]) + value
    print(name, env[name])


def _new_environment(add_executable_paths=[], add_library_paths=[]):
  env = dict(os.environ)
  _add_to_env_var_path_list(env, "PATH", add_executable_paths)
  _add_to_env_var_path_list(
    env, "PATH" if os.name == "nt" else "LD_LIBRARY_PATH", add_library_paths
  )
  return env


def _command_repr(command):
  return repr(" ".join([str(i) for i in command]))


def _non_zero_message(command, return_code):
  return "{} returned non-zero result: {}".format(_command_repr(command), return_code)


def run_command(
    *command,
    cwd=Path(),
    exit_on_error=False,
    add_executable_paths=[],
    add_library_paths=[],
    return_popen=False,
):
  error = None
  try:
    popen_kwargs = dict(
      cwd=str(cwd),
      stdout=sys.stdout,
      stderr=sys.stderr,
      env=_new_environment(add_executable_paths, add_library_paths),
    )
    if return_popen:
      return subprocess.Popen(command, **popen_kwargs)
    else:
      subprocess.run(command, check=True, **popen_kwargs)
  except OSError as os_error:
    error = "Could not run {}: {}".format(_command_repr(command), str(os_error))
    if not exit_on_error:
      raise RunCommandError(error) from os_error
  except subprocess.CalledProcessError as return_code_error:
    error = _non_zero_message(command, return_code_error.returncode)
    if not exit_on_error:
      raise RunCommandError(error) from return_code_error
  if exit_on_error and error is not None:
    sys.exit("ERROR: " + error)


def run_python(*args, **kwargs) -> None:
  return run_command(sys.executable, *args, **kwargs)


def wait_or_kill(proc, timeout):
  try:
    return_code = proc.wait(timeout=timeout)
  except subprocess.TimeoutExpired as ex:
    proc.kill()
    raise RunCommandError(
      f"Timedout, had to kill {proc.pid} " + _command_repr(proc.args)
    ) from ex
  if return_code != 0:
    raise RunCommandError(_non_zero_message(proc.args, return_code))


def run_cmake(*args):
  run_command("cmake", *args, exit_on_error=True)


def build_cmake_project(source_dir, build_dir, cfg_args=[], build_args=[]):
  if build_dir.exists():
    shutil.rmtree(build_dir)
  build_dir.mkdir()
  run_cmake(
    "-S",
    str(source_dir),
    "-B",
    str(build_dir),
    "-GNinja",  # cmake-build-extension provides Ninja
    f'-DCMAKE_MAKE_PROGRAM={shutil.which("ninja")}',
    f"-DCMAKE_BUILD_TYPE={build_type}",
    *cfg_args,
  )
  run_cmake("--build", str(build_dir), "--config", build_type, *build_args)
