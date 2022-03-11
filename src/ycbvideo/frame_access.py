import functools
import os
from pathlib import Path
import random
import re
from typing import Dict, Iterable, Iterator, List, NamedTuple, Optional, Sized, Tuple, Union

import imageio
from numpy import ndarray
import scipy.io

from . import utils


class Box(NamedTuple):
    label: str
    coordinates: Tuple[Tuple[float, float], Tuple[float, float]]


class Descriptor(NamedTuple):
    frame_sequence: str
    frame: str


class Frame(NamedTuple):
    color: ndarray
    depth: ndarray
    boxes: Optional[List[Box]]
    label: ndarray
    meta: Dict
    description: Descriptor


class FrameSequence:
    _FILE_PATTERN = re.compile(r'^(?P<index>[0-9]{6})-(?P<kindoffile>[a-z]+)\.(png|txt|mat)$')

    def __init__(self, path: Union[Path, str]):
        self._path = utils.validate_directory_path(path)
        self._sequence_name = self._path.name

    @functools.lru_cache()
    def get_available_frame_sets(self) -> Tuple[List[str], Dict[str, List[str]]]:
        files = os.listdir(self._path)

        frame_sets = {}
        for file in files:
            if match := FrameSequence._FILE_PATTERN.match(file):
                index = match.group('index')
                kind_of_file = match.group('kindoffile')

                if index not in frame_sets:
                    frame_sets[index] = set()

                frame_sets[index].add(kind_of_file)

        expected_kind_of_files = ['color', 'depth', 'label', 'meta']
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
            meta=scipy.io.loadmat(str(self._path / f"{index}-meta.mat")),
            description=Descriptor(self._path.name, index))

    def _get_boxes(self, index: str) -> List[Box]:
        file = self._path / f"{index}-box.txt"
        with open(file, 'r') as f:
            boxes = []

            for line in f:
                entries = line.split(' ')

                label = entries[0]
                x1, y1, x2, y2 = entries[1:]
                coordinates = ((float(x1), float(y1)),
                               (float(x2), float(y2)))

                boxes.append(Box(label, coordinates))

        return boxes


class FrameAccessor:
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

    def frames_info(self) -> Dict[str, Dict[str, Optional[List[str]]]]:
        available_sequences = sorted(self.get_available_frame_sequences())

        info = {}
        for sequence_identifier in available_sequences:
            sequence = self.get_frame_sequence(sequence_identifier)
            complete_frame_sets, incomplete_frame_sets = sequence.get_available_frame_sets()

            frame_sets = {}
            for complete_set in complete_frame_sets:
                frame_sets[complete_set] = None
            for identifier, incomplete_set in incomplete_frame_sets.items():
                frame_sets[identifier] = incomplete_set

            info[sequence_identifier] = frame_sets

        return info

    @functools.lru_cache()
    def get_frame_sequence(self, index: Union[str, int]) -> FrameSequence:
        if isinstance(index, int):
            index = "{:04d}".format(index)

        path = self._data_syn_directory if index == self._data_syn_directory.name else self._data_directory / index

        if index not in self.get_available_frame_sequences():
            raise IOError(f"Frame sequence does not exist: {index} ({path})")

        return FrameSequence(path)

    def get_frame(self, description: Tuple[Union[str, int], Union[str, int]]) -> Frame:
        """
        Return the frame specified by the given description.

        Parameters
        ----------
        description : Tuple[Union[str, int], Union[str, int]]
                      Description for the requested frame,
                      like e.g. a descriptor returned by
                      get_descriptors(expression_source)
        Returns
        -------
        Frame
            The frame specified by the given description,
            if it exists.
        """

        sequence_description, frame_description = description

        if not isinstance(sequence_description, (str, int)) or not isinstance(frame_description, (str, int)):
            raise TypeError('Sequence and frame description must be of type str or int')

        # handle possible ints
        sequence_description = str(sequence_description)
        frame_description = str(frame_description)

        sequence_index = (sequence_description if sequence_description == 'data_syn'
                          else utils.normalize_element(sequence_description, 'sequence'))
        frame_index = utils.normalize_element(frame_description, 'frame')

        return self.get_frame_sequence(sequence_index).get_frame(frame_index)


class FrameAccessObject(Sized, Iterable):
    def __init__(self, path: Union[Path, str], descriptors: List[Descriptor]):
        self._path = utils.validate_directory_path(path)
        self._frame_accessor = FrameAccessor(path)
        self._descriptors = descriptors

    def get_frame(self, descriptor: Descriptor) -> Frame:
        return self._frame_accessor.get_frame(descriptor)

    def get_descriptors(self) -> List[Descriptor]:
        return self._descriptors.copy()

    def shuffle(self):
        random.shuffle(self._descriptors)

    def __iter__(self) -> Iterator[Frame]:
        for descriptor in self._descriptors:
            yield self.get_frame(descriptor)

    def __len__(self):
        return len(self._descriptors)

    def __getitem__(self, index: int) -> Frame:
        if isinstance(index, int):
            if 0 <= index < len(self):
                return self.get_frame(self._descriptors[index])

            raise ValueError('index out of range')

        raise TypeError('item must be an int')
