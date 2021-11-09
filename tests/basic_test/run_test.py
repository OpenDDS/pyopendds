import sys
from pathlib import Path
import shutil
import argparse

from pyopendds.dev.util import RunCommandError, run_command, run_python, wait_or_kill


this_dir = Path(__file__).resolve().parent
timeout = 10


def run_test(args):
    build_dirname = 'build_cpp11' if args.cpp11 else 'build_classic'
    build_dir = this_dir / build_dirname

    if not args.just_run:
        # Remove any existing build dir
        if build_dir.exists():
            shutil.rmtree(build_dir)

        # Build C++ IDL Library and Publisher
        build_dir.mkdir()
        config_flags = []
        if args.cpp11:
            config_flags.append('-DCPP11_IDL=ON')
        run_command('cmake', '..', cwd=build_dir, exit_on_error=True)
        run_command('cmake', '--build', '.', cwd=build_dir, exit_on_error=True)

        # Generate and Install Python Package
        pack_dir = 'basic_output'
        run_command('itl2py', '-o', pack_dir, 'basic_idl', 'basic.itl',
            cwd=build_dir, exit_on_error=True)
        run_python('-m', 'pip', '--verbose', 'install', '.',
            cwd=(build_dir / pack_dir), exit_on_error=True)

    # Run the test
    pub = run_command(build_dir / 'publisher', '-DCPSConfigFile', 'rtps.ini',
        return_popen=True, cwd=this_dir)
    sub = run_python(this_dir / 'subscriber.py', cwd=this_dir, return_popen=True)
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
