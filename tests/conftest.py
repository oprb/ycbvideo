import os
from pathlib import Path
from typing import List, Set, Dict, Union
import shutil

import pytest


@pytest.fixture()
def incomplete_dataset(tmp_path):
    dataset = tmp_path / 'dataset'
    # path to the test data relative to the project root
    path_to_test_data = Path('data/tests/ycb_video_dataset')

    def _incomplete_dataset(missing_files: Dict[str, Set[str]]):
        """
        Provide access to an incomplete test dataset.

        Parameters
        ----------
        missing_files: Dict[str, Set[str]]
            Keys:   relative paths to directories in the test dataset,
                    for which at least one file should be missed
            Values: sets of files, which should be missed in the
                    corresponding directories
        """
        files_to_ignore = {}
        for directory in missing_files:
            # the src arguments to _get_files_to_ignore
            # are relative paths from the project root,
            # at least if the working directory is correctly
            # set to the project root, therefore the paths have
            # to be adjusted accordingly
            path_from_project_root = path_to_test_data / directory
            files_to_ignore[str(path_from_project_root)] = missing_files[directory]

        # names parameter is only declared to fulfill the expectation
        # on the shutil.copytree ignore parameter
        def _get_files_to_ignore(src: Union[os.PathLike, str], names: List[str]) -> Set[str]:
            # converting an os.PathLike-like object to get the
            # string representation of the corresponding path
            src_path = os.fsdecode(src)

            return files_to_ignore[src_path] if src_path in files_to_ignore else set()

        shutil.copytree('data/tests/ycb_video_dataset',
                        dataset,
                        ignore=_get_files_to_ignore)

        return dataset

    return _incomplete_dataset


@pytest.fixture(scope='session')
def dataset(tmp_path_factory):
    test_data = tmp_path_factory.mktemp('test_data')
    dataset = test_data / 'dataset'

    # should not be modified
    data_source = Path('data/tests/ycb_video_dataset')
    shutil.copytree(data_source, dataset)

    return dataset
