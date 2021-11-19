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


class FrameSelector(NamedTuple):
    frame_sequence_selection: str
    frame_selection: str


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


class YcbVideoLoader:
    def __init__(self, path: str, data_directory: str = 'data'):
        self._set_directory_path(path)
        self._data_directory = data_directory
        self._available_data_frame_sequences = self.get_available_frame_sequences()
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

    def get_available_frames(self, frame_sequence: str) -> List[str]:
        return [entry[:6] for entry in os.listdir(f"{self._path}/{self._data_directory}/{frame_sequence}") if entry.endswith('-color.png')]

    @staticmethod
    def get_frame_set_index(self, frame_set: Union[str, int]) -> str:
        if not isinstance(frame_set, str) or not isinstance(frame_set, int):
            raise TypeError("Index has to be of type 'str' or type 'int'")

        index = frame_set
        if isinstance(frame_set, str):
            if match := re.match(r'00(?P<index>[0-9]{2})', frame_set):
                index = int(match.group('index'))
            else:
                raise ValueError(f"Index has wrong format: {frame_set}")

        if not 0 <= frame_set <= 91:
            raise ValueError(f"Index has to be a value between 0 and 91: {frame_set}")

        return "{:04d}".format(frame_set)

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

    def get_frame(self, index: Union[str, Tuple[str, str]]) -> Frame:
        if isinstance(index, str):
            if match := re.match(r'^(?P<framesequence>[0-9]{4}):(?P<frame>[0-9]{6})$', index):
                frame_sequence = match.group('framesequence')
                frame = match.group('frame')

                index = (frame_sequence, frame)
            else:
                raise ValueError(f"Invalid pattern (<frame_sequence>:<frame> required): {index}")

        return self.get_frame_sequence(index[0]).get_frame(index[1])

    @staticmethod
    def _get_items(selection: str) -> List[str]:
        list_pattern = re.compile(r'^\[(?P<items>[0-9]+(,[0-9]+)*)\]$')
        single_item_pattern = re.compile(r'^(?P<item>[0-9]+|\*)$')

        items = []
        if match := list_pattern.match(selection):
            items = [item for item in match.group('items').split(',')]
        elif match := single_item_pattern.match(selection):
            items.append(match.group('item'))
        else:
            raise ValueError(f"Descriptor syntax is incorrect: {selection}")

        return items

    @staticmethod
    def _format_selection_item(item: str, kind_of_item: str) -> str:
        if not (kind_of_item == 'frame_sequence' or kind_of_item == 'frame'):
            raise ValueError(
                f"Unknown kind of descriptor (has to be either 'frame_sequence' or 'frame'): {kind_of_item}")
        if item == '*':
            return item

        return "{:04d}".format(int(item)) if kind_of_item == 'frame_sequence' else\
            "{:06d}".format(int(item))

    @staticmethod
    def get_frame_selector(selection: str) -> FrameSelector:
        selection_pattern = r'\[([0-9]{1,n}(,[0-9]{1,n})*)\]|([0-9]{1,n})|\*'
        frameset_selection_pattern = selection_pattern.replace('n', '4')
        frame_selection_pattern = selection_pattern.replace('n', '6')
        combined_pattern = re.compile(
            f"^(?P<frameset>{frame_selection_pattern}):(?P<frame>{frameset_selection_pattern})$")

        if match := combined_pattern.match(selection):
            frame_set_selection = match.group('frameset')
            frame_selection = match.group('frame')

            return FrameSelector(frame_set_selection, frame_selection)
        else:
            raise ValueError(f"Selection syntax is incorrect: '{selection}'")

    @staticmethod
    def get_frame_selectors(selections: List[str]) -> List[FrameSelector]:
        frame_selectors = []

        for index, selection in enumerate(selections):
            try:
                frame_selectors.append(YcbVideoLoader.get_frame_selector(selection))
            except ValueError:
                raise ValueError(
                    f"Selection syntax is incorrect: Selection '{selection}' at index {index}") from ValueError

        return frame_selectors

    def get_frame_descriptors(self, frame_selector: FrameSelector) -> List[FrameDescriptor]:
        frame_descriptors = []

        frame_sequence_selection = YcbVideoLoader._get_items(frame_selector.frame_sequence_selection)
        frame_selection = YcbVideoLoader._get_items(frame_selector.frame_selection)

        actual_frame_sequence_selection = None
        actual_frame_selection = None

        if YcbVideoLoader._is_star_selection(frame_sequence_selection):
            actual_frame_sequence_selection = sorted(self._available_data_frame_sequences)
        else:
            actual_frame_sequence_selection = [YcbVideoLoader._format_selection_item(frame_sequence, 'frame_sequence') for
                                               frame_sequence in frame_sequence_selection]
            for index, frame_sequence in enumerate(actual_frame_sequence_selection):
                if frame_sequence not in self._available_data_frame_sequences:
                    raise ValueError(
                        f"""Data Frame Sequence is not available: {frame_sequence}
                            (specified at index {index} in {frame_selector}""")

        for frame_sequence in actual_frame_sequence_selection:
            available_frames = sorted(self.get_available_frames(frame_sequence))

            if YcbVideoLoader._is_star_selection(frame_selection):
                frame_descriptors.extend([FrameDescriptor(frame_sequence, frame) for frame in available_frames])

                continue
            else:
                actual_frame_selection = [YcbVideoLoader._format_selection_item(frame, 'frame') for
                                          frame in frame_selection]

            for index, frame in enumerate(actual_frame_selection):
                if frame not in available_frames:
                    raise ValueError(
                        f"""Data Frame is not available: {frame_sequence}:{frame}
                            (specified at index {index} in {frame_selector}""")

                frame_descriptors.append(FrameDescriptor(frame_sequence, frame))

        return frame_descriptors

    def _get_frame(self, descriptor: FrameDescriptor) -> Frame:
        return self.get_frame_sequence(descriptor.frame_sequence).get_frame(descriptor.frame)

    @staticmethod
    def _is_star_selection(selection: List[str]) -> bool:
        return len(selection) == 1 and selection[0] == '*'

    def frames(self, frames: List[str]) -> Iterable[Frame]:
        frame_descriptors = self._get_descriptors_from_selections(frames)

        for descriptor in frame_descriptors:
            yield self._get_frame(descriptor)

    def _get_descriptors_from_selections(self, selections: List[str]) -> List[FrameDescriptor]:
        frame_descriptors = []

        for selector in self.get_frame_selectors(selections):
            frame_descriptors.extend(self.get_frame_descriptors(selector))

        return frame_descriptors
