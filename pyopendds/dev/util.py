import sys
import subprocess
from pathlib import Path


class RunCommandError(Exception):
    pass


def run_command(*command, cwd=Path(), exit_on_error=False):
    error = None
    try:
        subprocess.run(
            command,
            check=True,
            cwd=str(cwd),
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except OSError as os_error:
        error = 'Could not run "{}": {}'.format(' '.join(command), str(os_error))
        if not exit_on_error:
            raise RunCommandError(error) from os_error
    except subprocess.CalledProcessError as return_code_error:
        error = '"{}" returned non-zero result: {}'.format(
            ' '.join(command), return_code_error.returncode)
        if not exit_on_error:
            raise RunCommandError(error) from return_code_error
    if exit_on_error and error is not None:
        sys.exit(error)


def run_python(*args, **kwargs):
    run_command(sys.executable, *args, **kwargs)
