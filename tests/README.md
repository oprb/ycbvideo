# Tests

Make sure *pytest* is installed.
Now, you can run the test from the *project root directory*, e.g. `python -m pytest -v`.
If you want to run the tests from e.g. *Pycharm*, add a *pytest Run Configuration*, where you set
the working directory to the project root directory.

In `tests/conftest.py`, some pytest fixtures are defined. If the working directory is not correctly
set before running the tests, copying of the test data to a temporary test directory will fail.