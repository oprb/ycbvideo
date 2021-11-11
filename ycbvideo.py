import imageio
import os
from collections import namedtuple
from typing import List, Union


FrameSet = namedtuple('FrameSet', ['color', 'depth', 'label'])


class DataSequence:
    def __init__(self, path: str):
        self._path = path
        self.test = os.listdir(self._path)

    def get_available_frame_sets(self) -> List[str]:
        return [entry[:6] for entry in os.listdir(self._path) if entry.endswith('-color.png')]

    def get_frame_set(self, index: Union[int, str]) -> FrameSet:
        if isinstance(index, int):
            index = "{:06d}".format(index)
        if index not in self.get_available_frame_sets():
            raise IOError(f"Frame set does not exist: {index}")

        partial_path = f"{self._path}/{index}-"

        return FrameSet(
            color=imageio.imread(partial_path + 'color.png'),
            depth=imageio.imread(partial_path + 'depth.png'),
            label=imageio.imread(partial_path + 'label.png'))


class YcbVideoLoader:
    def __init__(self, path: str, data_directory: str = 'data'):
        self._set_directory_path(path)
        self._data_directory = data_directory
    """
        path: Path to the YCB-Video dataset root directory
    """

    @staticmethod
    def _has_trailing_slash(path_to_folder: str):
        return path_to_folder.endswith('/')

    # def _remove_trailing

    def _set_directory_path(self, path: str):
        if not os.path.exists(path):
            raise IOError(f"Path does not exist: {path}")
        if not os.path.isdir(path):
            raise IOError(f"Path is not a directory: {path}")

        self._path = path[:-1] if YcbVideoLoader._has_trailing_slash(path) else path

    def get_available_data_sequences(self) -> List[str]:
        return os.listdir(f"{self._path}/{self._data_directory}")

    def get_data_sequence(self, index: Union[str, int]) -> DataSequence:
        if isinstance(index, int):
            index = "{:04d}".format(index)
        if index not in self.get_available_data_sequences():
            raise IOError(f"Data sequence does not exist: {index} ({self._path}/{self._data_directory}/{index})")

        return DataSequence(f"{self._path}/{self._data_directory}/{index}")
