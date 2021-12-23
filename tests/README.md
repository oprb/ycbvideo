# Tests

* Make sure *pytest* is installed.
* Make sure your *venv* is activated: Assuming the venv folder is named `venv`, just run
  `. venv/bin/activate` on a Linux system.
* Install the package with `pip install -e .`. If you want to test a source (ycbvideo-\*.tar.gz)
  or a wheel distribution (ycbvideo-\*-py3-none-any.whl) from the *dist* folder, install it by
  `pip install dist/ycbvideo-*.tar.gz` or `pip install dist/ycbvideo-*-py3-none-any.whl`.
  Uninstall any already installed version of ycbvideo beforehand with `pip uninstall ycbvideo`.

Now, you can run the test from the *project root directory*, e.g. `python -m pytest -v`.
If you want to run the tests from e.g. *Pycharm*, add a *pytest Run Configuration*, where you set
the working directory to the project root directory.

In `tests/conftest.py`, some pytest fixtures are defined. If the working directory is not correctly
set before running the tests, copying of the test data to a temporary test directory will fail.
