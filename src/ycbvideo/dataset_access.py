import functools
import os
from pathlib import Path
from typing import List, Union

from . import datatypes, utils


class DatasetAccess:
    def __init__(self, path: Union[Path, str]):
        self._path = utils.validate_directory_path(path)
        self._data_directory = self._path / 'data'
        self._data_syn_directory = self._path / 'data_syn'

    def get_available_data_frame_sequences(self) -> List[str]:
        return os.listdir(self._data_directory)

    def get_available_frame_sequences(self) -> List[str]:
        available_sequences = self.get_available_data_frame_sequences()

        if self._data_syn_directory.exists():
            available_sequences.append(self._data_syn_directory.name)

        return available_sequences

    @functools.lru_cache()
    def get_frame_sequence(self, index: Union[str, int]) -> datatypes.FrameSequence:
        if isinstance(index, int):
            index = "{:04d}".format(index)

        path = self._data_syn_directory if index == self._data_syn_directory.name else self._data_directory / index

        if index not in self.get_available_frame_sequences():
            raise IOError(f"Frame sequence does not exist: {index} ({path})")

        return datatypes.FrameSequence(path)
