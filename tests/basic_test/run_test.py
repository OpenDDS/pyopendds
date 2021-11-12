import sys
from pathlib import Path
import argparse

from pyopendds.dev.util import (
    RunCommandError,
    run_command,
    run_python,
    wait_or_kill,
    build_cmake_project,
)


this_dir = Path(__file__).resolve().parent
timeout = 10


def run_test(args):
    build_dirname = 'build_cpp11' if args.cpp11 else 'build_classic'
    build_dir = this_dir / build_dirname

    if not args.just_run:
        cfg_args = []
        if args.cpp11:
            cfg_args.append('-DCPP11_IDL=ON')
        build_cmake_project(this_dir, build_dir, cfg_args=cfg_args)

        # Generate and Install Python Package
        pack_dir = 'basic_output'
        run_command('itl2py', '-o', pack_dir, 'basic_idl', 'basic.itl',
            cwd=build_dir, exit_on_error=True)
        run_python('-m', 'pip', '--verbose', 'install', '.',
            cwd=(build_dir / pack_dir), exit_on_error=True)

    # Run the test
    pub = run_command(build_dir / 'publisher', '-DCPSConfigFile', 'rtps.ini',
        return_popen=True, cwd=this_dir,
        add_library_paths=[build_dir])
    sub = run_python(this_dir / 'subscriber.py', cwd=this_dir, return_popen=True,
        add_library_paths=[build_dir])
    wait_or_kill(pub, timeout)
    wait_or_kill(sub, timeout)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--cpp11', action='store_true')
    arg_parser.add_argument('--just-run', action='store_true')
    try:
        run_test(arg_parser.parse_args())
    except RunCommandError as ex:
        sys.exit(f'ERROR: {ex}')
