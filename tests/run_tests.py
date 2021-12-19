import sys
from pathlib import Path

from pyopendds.dev.util import run_command, run_python, RunCommandError


tests_path = Path(__file__).resolve().parent
unit_tests_path = tests_path / 'unit_tests'
pyopendds_path = tests_path.parent


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

    failed |= run_test(tests_path / 'basic_test')
    failed |= run_test(tests_path / 'basic_test', '--cpp11')

    return failed


def run_clang_format():
    template_dir = pyopendds_path / 'pyopendds/dev/itl2py/templates'
    assert template_dir.is_dir()
    all_files = list(pyopendds_path.glob('**/*.cpp')) + list(pyopendds_path.glob('**/*.hpp'))
    failed = False
    for file in all_files:
        if any([s.startswith('build') for s in file.parts]):
            if 'CMakeFiles' in file.parts:
                continue
            elif file.name.endswith('TypeSupportImpl.cpp'):
                continue
            elif file.name.endswith('C.cpp'):
                continue
            continue  # TODO: Remove, fix issues with generated code
        elif template_dir in file.parents:
            continue
        p = file.relative_to(pyopendds_path)
        try:
            run_command('clang-format', '--Werror', '--dry-run', str(p))
        except RunCommandError as e:
            print(str(p), 'failed:', str(e), file=sys.stderr)
            failed = True
    if failed:
        print('Run `clang-format -i FILE` for each file', file=sys.stderr)
    return failed


def run_all_tests():
    failed = False

    failed |= run_unit_tests()
    failed |= run_integration_tests()
    failed |= run_clang_format()

    if failed:
        sys.exit('There were test failures!')


if __name__ == '__main__':
    run_all_tests()
