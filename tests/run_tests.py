import sys
from pathlib import Path

from pyopendds.dev.util import run_python, RunCommandError


tests_path = Path(__file__).resolve().parent
unit_tests_path = tests_path / 'unit_tests'


def run_unit_tests():
    print('Running unit tests...')
    try:
        run_python('-m', 'unittest', '--verbose', cwd=unit_tests_path)
    except RunCommandError as e:
        print('Unit tests failed:', str(e), file=sys.stderr)
        return True
    return False


def run_test(dir_path, *args):
    command = [str(dir_path / 'run_test.py')] + list(args)
    s = repr(' '.join(command))
    print('Running', s, '...')
    try:
        run_python(*command, cwd=dir_path)
    except RunCommandError as e:
        print(s, 'failed:', str(e), file=sys.stderr)
        return True
    return False


def run_integration_tests():
    failed = False

    return failed


def run_all_tests():
    failed = False

    failed |= run_unit_tests()
    failed |= run_integration_tests()

    if failed:
        sys.exit('There were test failures!')


if __name__ == '__main__':
    run_all_tests()
