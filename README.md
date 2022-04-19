# Re-enabling GitHub Actions

After a certain period of time (currently 60 days) without commits GitHub
automatically disables Actions. They can be re-enabled manually per repository.
This script does this for all gocept repositories listed in `repositories.txt`.
It does no harm if Actions is already enabled for a repository.

## Preparation

* Install GitHub's CLI application, see https://github.com/cli/cli.

* Authorize using the application:

  - ``gh auth login``

## Usage

To run the script just call it::

    $ python3 re-enable-gha.py

Currently this has to be done manually once a while.

## Add new repository or remove repository

To add or remove a repository change `repositories.txt` and commit the change.
