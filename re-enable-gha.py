#!/bin/env python3
import argparse
import pathlib
import subprocess  # nosec
import sys


org = 'gocept'
base_url = f'https://github.com/{org}'
base_path = pathlib.Path(__file__).parent


def list_packages(path: pathlib.Path) -> list:
    """List the packages in ``path``."""
    return [
        p
        for p in path.read_text().split('\n')
        if p and not p.startswith('#')
    ]


def abort(exitcode):
    """Ask the user to abort."""
    print('ABORTING: Please fix the errors shown above.')
    print('Proceed anyway (y/N)?', end=' ')
    if input().lower() != 'y':
        sys.exit(exitcode)


def call(*args, capture_output=False, cwd=None):
    """Call `args` as a subprocess.

    If it fails exit the process.
    """
    result = subprocess.run(  # nosec
        args, capture_output=capture_output, text=True, cwd=cwd)
    if result.returncode != 0:
        abort(result.returncode)
    return result


def run_workflow(base_url, org, repo):
    """Manually start the tests.yml workflow of a repository."""
    result = call('gh', 'workflow', 'run', 'tests.yml', '-R', f'{org}/{repo}')
    if result.returncode != 0:
        print('To enable manually starting workflows clone the repository'
              ' and add `workflow_dispatch:` to tests.yml -> "on:".')
        print('Command to clone:')
        print(f'git clone {base_url}/{repo}.git')
        return False
    return True


parser = argparse.ArgumentParser(
    description='Re-enable GitHub Actions for all repos in a repositories.txt.'
)
parser.add_argument(
    '--force-run',
    help='Run workflow even it is already enabled.',
    action='store_true')
args = parser.parse_args()
repos = list_packages(base_path / 'repositories.txt')

for repo in repos:
    print(repo)
    wfs = call(
        'gh', 'workflow', 'list', '--all', '-R', f'{org}/{repo}',
        capture_output=True).stdout
    test_line = [x for x in wfs.splitlines() if x.startswith('test')][0]
    if 'disabled_inactivity' not in test_line:
        print('    ☑️  already enabled')
        if args.force_run:
            run_workflow(base_url, org, repo)
        continue
    test_id = test_line.split()[-1]
    call('gh', 'workflow', 'enable', test_id, '-R', f'{org}/{repo}')
    if run_workflow(base_url, org, repo):
        print('    ✅ enabled')
