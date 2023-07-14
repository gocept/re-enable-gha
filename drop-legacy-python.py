#!/usr/bin/env python3
import argparse
import contextlib
import os
import pathlib
import shutil
import subprocess  # nosec
import sys


@contextlib.contextmanager
def change_dir(path):
    """Change current working directory temporarily to `path`.

    Yields the current working directory before the change.
    """
    cwd = os.getcwd()
    try:
        os.chdir(path)
        yield cwd
    finally:
        os.chdir(cwd)


def wait_for_accept():
    """Wait until the user has hit enter."""
    print('Proceed by hitting <ENTER>')
    input()


def git_branch(branch_name) -> bool:
    """Switch to existing or create new branch.

    Return `True` if updating.
    """
    branches = call(
        'git', 'branch', '--format', '%(refname:short)',
        capture_output=True).stdout.splitlines()
    if branch_name in branches:
        call('git', 'checkout', branch_name)
        updating = True
    else:
        call('git', 'checkout', '-b', branch_name)
        updating = False
    return updating


def abort(exitcode):
    """Ask the user to abort."""
    print('ABORTING: Please fix the errors shown above.')
    print('Proceed anyway (y/N)?', end=' ')
    if input().lower() != 'y':
        sys.exit(exitcode)


def call(*args, capture_output=False, cwd=None, allowed_return_codes=(0, )):
    """Call `args` as a subprocess.

    If it fails exit the process.
    """
    result = subprocess.run(  # nosec
        args, capture_output=capture_output, text=True, cwd=cwd)
    if result.returncode not in allowed_return_codes:
        abort(result.returncode)
    return result


parser = argparse.ArgumentParser(
    description='Drop support of Python 2.7 up to 3.6 from a package.')
parser.add_argument(
    'path', type=pathlib.Path, help='path to the repository to be configured')
parser.add_argument(
    '--branch',
    dest='branch_name',
    default=None,
    help='Define a git branch name to be used for the changes. If not given'
         ' it is constructed automatically and includes the configuration'
         ' type')

args = parser.parse_args()
path = args.path.absolute()

if not (path / '.git').exists():
    raise ValueError('`path` does not point to a git clone of a repository!')

with change_dir(path) as cwd_str:
    branch_name = 'drop-legacy-python'
    updating = git_branch(branch_name)

    call(shutil.which('bumpversion'), '--breaking', '--no-input')
    call(shutil.which('addchangelogentry'),
         'Drop support for Python 2.7, 3.5, 3.6.', '--no-input')
    print('Fix change log.')
    call(os.environ['EDITOR'], 'CHANGES.rst')
    call(shutil.which('check-python-versions'),
         '--drop=2.7,3.5,3.6', '--only=setup.py')

    config_package_args = [
        sys.executable,
        'config-package.py',
        path,
        f'--branch={branch_name}',
        '--no-push',
    ]
    print('Remove legacy Python (2.7-3.6 + PyPy2, coverage-python-version)'
          ' settings from tests.yml')
    call(os.environ['EDITOR'], '.github/workflows/tests.yml')
    print('Update `pypy3` to `pypy-3.9` and use `ubuntu-latest` in tests.yml')
    call(os.environ['EDITOR'], '.github/workflows/tests.yml')
    print('Update to: `actions/checkout@v3`, `actions/setup-python@v4`,'
          ' `actions/cache@v3`.')
    call(os.environ['EDITOR'], '.github/workflows/tests.yml')
    print('Remove legacy Python (2.7-3.6 + PyPy2, coverage-python-version)'
          ' settings from tox.ini')
    call(os.environ['EDITOR'], 'tox.ini')
    print('Remove `six` from the list of dependencies and other Py 2 things.')
    call(os.environ['EDITOR'], 'setup.py')
    print("Add `python_requires='>=3.7',`")
    call(os.environ['EDITOR'], 'setup.py')
    src = path.resolve() / 'src'
    call('find', src, '-name', '*.py', '-exec',
         shutil.which('pyupgrade'), '--py3-plus', '--py37-plus', '{}', ';')
    call(shutil.which('pyupgrade'), '--py3-plus', '--py37-plus', 'setup.py',
         allowed_return_codes=(0, 1))

    excludes = ('--exclude-dir', '__pycache__', '--exclude-dir', '*.egg-info',
                '--exclude', '*.pyc', '--exclude', '*.so')
    print(
        'Replace all remaining `six` mentions or continue if none are listed.')
    call('grep', '-rn', 'six', src, *excludes, allowed_return_codes=(0, 1))
    wait_for_accept()
    print('Replace any remaining code that may support legacy Python 2:')
    call('egrep', '-rn',
         '2.7|3.5|3.6|sys.version|PY2|PY3|Py2|Py3|Python 2|Python 3'
         '|__unicode__|ImportError', src, *excludes,
         allowed_return_codes=(0, 1))
    wait_for_accept()
    tox_path = shutil.which('tox')
    call(tox_path, '-p', 'auto')
    print('Adding, committing and pushing all changes ...')
    call('git', 'add', '.')
    call('git', 'commit', '-m', 'Drop support for Python 2.7 up to 3.6.')
    call('git', 'push', '--set-upstream', 'origin', branch_name)
    if updating:
        print('Updated the previously created PR.')
    else:
        print('If everything went fine up to here:')
        print('Create a PR, using the URL shown above.')
