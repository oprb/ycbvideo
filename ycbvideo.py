import imageio
from numpy import ndarray
import os
import re
import logging
from typing import List, Tuple, NamedTuple, Iterable, Union


class Box(NamedTuple):
    label: str
    coordinates: Tuple[float, float, float, float]


class Frame(NamedTuple):
    color: ndarray
    depth: ndarray
    boxes: List[Box]
    label: ndarray


class FrameSequence:
    def __init__(self, path: str):
        self._path = path
        self.test = os.listdir(self._path)

    def get_available_frame_sets(self) -> List[str]:
        return [entry[:6] for entry in os.listdir(self._path) if entry.endswith('-color.png')]

    def __len__(self):
        return len(self.get_available_frame_sets())

    def get_frame(self, index: Union[int, str]) -> Frame:
        if isinstance(index, int):
            index = "{:06d}".format(index)
        if index not in self.get_available_frame_sets():
            raise IOError(f"Frame set does not exist: {index}")

        partial_path = f"{self._path}/{index}-"

        return Frame(
            color=imageio.imread(partial_path + 'color.png'),
            depth=imageio.imread(partial_path + 'depth.png'),
            boxes=self._get_boxes(index),
            label=imageio.imread(partial_path + 'label.png'))

    def _get_boxes(self, index: str) -> List[Box]:
        file = f"{self._path}/{index}-box.txt"
        with open(file, 'r') as f:
            pattern = re.compile(r'^(?P<label>[^ ]+) ([0-9.]+) ([0-9.]+) ([0-9.]+) ([0-9.]+)$')
            boxes =[]

            for line in f:
                if match := pattern.match(line):
                    label = match.group(1)
                    coordinates = (float(match.group(2)),
                                   float(match.group(3)),
                                   float(match.group(4)),
                                   float(match.group(5)))
                    boxes.append(Box(label, coordinates))
                else:
                    raise ValueError(f"Box file has invalid format: {file}")

        return boxes


class YcbVideoLoader:
    def __init__(self, path: str, data_directory: str = 'data'):
        self._set_directory_path(path)
        self._data_directory = data_directory
    """
        path: Path to the YCB-Video dataset root directory
    """

    def _set_directory_path(self, path: str):
        if not os.path.exists(path):
            raise IOError(f"Path does not exist: {path}")
        if not os.path.isdir(path):
            raise IOError(f"Path is not a directory: {path}")

        self._path = path.rstrip('/')

    def get_available_frame_sequences(self) -> List[str]:
        return os.listdir(f"{self._path}/{self._data_directory}")

    def get_frame_sequence(self, index: Union[str, int]) -> FrameSequence:
        if isinstance(index, int):
            index = "{:04d}".format(index)
        if index not in self.get_available_frame_sequences():
            raise IOError(f"Data sequence does not exist: {index} ({self._path}/{self._data_directory}/{index})")

        return FrameSequence(f"{self._path}/{self._data_directory}/{index}")

    def get_frame_sequences(self, indexes: Iterable[Union[int, str]]) -> List[FrameSequence]:
        return [self.get_frame_sequence(index) for index in indexes]

    def get_frames(self, indexes: Iterable[int],
                   frame_sequence_indexes: Iterable[Union[int, str]] = None) -> Iterable[Frame]:
        if frame_sequence_indexes is None:
            frame_sequence_indexes = sorted(self.get_available_frame_sequences())

        indexes = sorted(indexes, reverse=True)

        frames = []
        absolute_index = 0
        for frame_sequence in (self.get_frame_sequence(index) for index in frame_sequence_indexes):
            sequence_length = len(frame_sequence)
            while indexes and (relative_index := indexes[-1] - absolute_index) <= sequence_length:
                frames.append(frame_sequence.get_frame(relative_index))
                indexes.pop()

            absolute_index += sequence_length

        if indexes:
            logging.warning(f"All frame sets are traversed but still indexes remaining: {indexes}")

        return frames
