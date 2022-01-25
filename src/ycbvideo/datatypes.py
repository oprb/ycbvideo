import functools
import os
from pathlib import Path
import re
from typing import Union, NamedTuple, Tuple, List, Dict, Optional

import imageio
from numpy import ndarray

from . import utils

FILE_PATTERN = re.compile(r'^(?P<index>[0-9]{6})-(?P<kindoffile>[a-z]+)\.(png|txt)$')
BOUNDING_BOX_PATTERN = re.compile(r'^(?P<label>[^ ]+) ([0-9.]+) ([0-9.]+) ([0-9.]+) ([0-9.]+)$')


class Box(NamedTuple):
    label: str
    coordinates: Tuple[float, float, float, float]


class Descriptor(NamedTuple):
    frame_sequence: str
    frame: str


class Frame(NamedTuple):
    color: ndarray
    depth: ndarray
    boxes: Optional[List[Box]]
    label: ndarray
    description: Descriptor


class FrameSequence:
    def __init__(self, path: Union[Path, str]):
        self._path = utils.validate_directory_path(path)
        self._sequence_name = self._path.name

    @functools.lru_cache()
    def get_available_frame_sets(self) -> Tuple[List[str], Dict[str, List[str]]]:
        files = os.listdir(self._path)

        frame_sets = {}
        for file in files:
            if match := FILE_PATTERN.match(file):
                index = match.group('index')
                kind_of_file = match.group('kindoffile')

                if index not in frame_sets:
                    frame_sets[index] = set()

                frame_sets[index].add(kind_of_file)

        expected_kind_of_files = ['color', 'depth', 'label']
        if self._sequence_name != 'data_syn':
            expected_kind_of_files.append('box')

        complete_frame_sets = []
        incomplete_frame_sets = {}
        for frame_set, kind_of_files in frame_sets.items():
            missing_kinds_of_file = []

            for kind_of_file in expected_kind_of_files:
                if kind_of_file not in kind_of_files:
                    missing_kinds_of_file.append(kind_of_file)

            if missing_kinds_of_file:
                incomplete_frame_sets[frame_set] = missing_kinds_of_file
            else:
                complete_frame_sets.append(frame_set)

        return complete_frame_sets, incomplete_frame_sets

    def get_complete_frame_sets(self) -> List[str]:
        complete_frame_sets, _ = self.get_available_frame_sets()

        return complete_frame_sets

    def get_incomplete_frame_sets(self) -> Dict[str, List[str]]:
        _, incomplete_frame_sets = self.get_available_frame_sets()

        return incomplete_frame_sets

    def __len__(self):
        return len(self.get_complete_frame_sets())

    def get_frame(self, index: Union[int, str]) -> Frame:
        if isinstance(index, int):
            index = "{:06d}".format(index)

        if index in (incomplete_frame_sets := self.get_incomplete_frame_sets()):
            raise IOError(f"Frame set is not complete: {index} Missing: {incomplete_frame_sets[index]}")
        if index not in self.get_complete_frame_sets():
            raise IOError(f"Frame set does not exist: {index}")

        return Frame(
            color=imageio.imread(self._path / f"{index}-color.png"),
            depth=imageio.imread(self._path / f"{index}-depth.png"),
            boxes=self._get_boxes(index) if self._sequence_name != 'data_syn' else None,
            label=imageio.imread(self._path / f"{index}-label.png"),
            description=Descriptor(self._path.name, index))

    def _get_boxes(self, index: str) -> List[Box]:
        file = self._path / f"{index}-box.txt"
        with open(file, 'r') as f:
            boxes = []

            for line in f:
                if match := BOUNDING_BOX_PATTERN.match(line):
                    label = match.group(1)
                    coordinates = (float(match.group(2)),
                                   float(match.group(3)),
                                   float(match.group(4)),
                                   float(match.group(5)))
                    boxes.append(Box(label, coordinates))
                else:
                    raise ValueError(f"Box file has invalid format: {file}")

        return boxes
