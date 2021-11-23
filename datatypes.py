import re
import imageio
import os
from numpy import ndarray
from typing import Union, NamedTuple, Tuple, List


class Box(NamedTuple):
    label: str
    coordinates: Tuple[float, float, float, float]


class Frame(NamedTuple):
    color: ndarray
    depth: ndarray
    boxes: List[Box]
    label: ndarray


class FrameDescriptor(NamedTuple):
    frame_sequence: str
    frame: str


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