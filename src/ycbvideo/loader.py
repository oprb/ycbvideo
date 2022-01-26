import functools
import os
from pathlib import Path
import random
from typing import List, Iterable, Union, Dict, Optional, Sequence

from . import datatypes, parsing, selectors, utils


def _load_selection_expressions_from_file(file: Union[Path, str]) -> List[str]:
    file_path = Path(file)

    if not file_path.exists():
        raise IOError(f"File does not exist: {file_path}")

    expressions = []
    with open(file_path, 'r') as f:
        for line_number, line in enumerate(f):
            # skip empty lines and remove leading and trailing whitespace including 'newline'
            if stripped_line := line.lstrip().rstrip():
                expressions.append(stripped_line)

    return expressions


class Loader:
    def __init__(self, path: Union[Path, str]):
        self._path = utils.validate_directory_path(path)
        self._data_directory = self._path / 'data'
        self._data_syn_directory = self._path / 'data_syn'
        self._available_frame_sequences = self.get_available_frame_sequences()

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

    def _get_descriptors(self, expressions: List[str]) -> List[datatypes.Descriptor]:
        selectors = parsing.parse_selection_expressions(expressions)

        descriptors = []
        for selector in selectors:
            descriptors.extend(self._create_descriptors_from_selector(selector))

        return descriptors

    def _create_descriptors_from_selector(self, selector: selectors.Selector) -> List[datatypes.Descriptor]:
        available_sequences = sorted(self.get_available_frame_sequences())

        descriptors = []
        try:
            selected_sequences = selector.select_sequences(available_sequences)
        except selectors.MissingElementError as error:
            raise IOError(f"Frame sequence is not available: {error.element}")

        for sequence in selected_sequences:
            sequence_object = self.get_frame_sequence(sequence)
            available_frames = sorted(sequence_object.get_complete_frame_sets())

            try:
                selected_frames = selector.select_frames(available_frames)
            except selectors.MissingElementError as error:
                frame = error.element
                if frame in (incomplete_frame_sets := sequence_object.get_incomplete_frame_sets()):
                    missing_files = incomplete_frame_sets[frame]

                    raise IOError(f"Files for frame missing: {sequence}/{frame} misses {missing_files}")
                else:
                    raise IOError(f"Frame is not available: {sequence}/{frame}")

            for frame in selected_frames:
                descriptors.append(datatypes.Descriptor(sequence, frame))

        return descriptors

    def frames(self, frames: Union[List[str], Union[Path, str]], shuffle: bool = False) -> Iterable[datatypes.Frame]:
        """
        Return an iterable object for the specified frames.

        To be memory-friendly, the specified frames will be created
        just-in-time. The frames can be specified as either a list of
        selection expressions or as a path to a file with one selection
        expression per line.
        Frame sequences and frames can each be selected by an
        expression containing
            - a single element
            - a list of comma-delimited elements
            - a range of elements similar to slicing works in Python
            - a '*' expressing all available elements.
        Also, 'data_syn' can be used as a frame sequence selection
        element to specify the data_syn frame sequence.
        To get all available frame sequences except for data_syn,
        'data' can be specified as a frame sequence selection
        element.
        A frame sequence selection expression and a frame selection
        expression together form a selection expression. Between both
        frame sequence selection expression and frame selection
        expression, a '/' is placed as the delimiter.

        Examples for valid selection expressions:
            - '1/42'
                Get the 42th frame from the 1st frame sequence
            - '1/[1,2,3]'
                Get the 1st, 2nd and 3th frame from the 1st frame
                sequence
            - '[1,2]/42'
                Get the 42th frame from the 1st and 2nd frame
                sequence each
            - '[1,2]/[4,3]'
                Get the 4th and 3rd frame from the 1st and 2nd frame
                sequence each
            - '[1,2]/*'
                Get all available frames from the 1st and 2nd frame
                sequence each
            - '*/[3,4]'
                Get the 3rd and 4th frame from each the available
                frame sequences
            - '*/*'
                Get all available frames from each the available
                frame sequences
            - 'data_syn/[1,2]'
                Get the 1st and 2nd frame from the data_syn frame
                sequence
            - 42:56:1/1
                Get the 1st frame from each frame sequence between frame
                sequence 42 (inclusive) and 56 (exclusive) by taking steps
                of length 1, i.e. when frame sequence 42 to frame sequence
                55 all are available, 14 frames would be selected
            - 42/::-2
                Get every other frame from frame sequence 42 in reverse
                order from all available frames of frame sequence 42

        If `shuffle` is set to 'False', the frames will be returned
        in exactly the order as specified by the order of selection
        expressions and the order of the elements in those. Otherwise,
        the frames get shuffled. Since random.shuffle() is used to
        shuffle the frames, by setting a seed with random.seed() or
        setting a state with random.setstate() a certain shuffle order
        can be defined.

        For each specified frame it is made sure that the corresponding
        files exists, even if the frame is only eventually created.
        This can be especially useful when specifying a large number of
        frames and consuming them needs minutes or even hours e.g. in
        a machine-learning context.

        Parameters
        ----------
        frames : Union[List[str], Union[pathlib.Path, str]]
            Either a list of selection expressions or a path to a file
            containing selection expressions.
            The path can be either a string or a Path object.
            If path is not absolute, it is assumed to be relative to
            the root of the dataset.
        shuffle : bool, optional
            If True, the selected frames get shuffled

        Returns
        ------
        Iterable[Frame]
            An iterable allowing access to the frame objects with
            additional support for the builtin len(iterable) and
            for accessing single frame objects from it by specifying
            an int index e.g. iterable[42]
        """

        if isinstance(frames, list):
            if not frames:
                raise ValueError('List is empty')
            frame_descriptors = self._get_descriptors(frames)
        elif isinstance(frames, (Path, str)):
            path = Path(frames)

            if not path.is_absolute():
                path = self._path / path

            if not path.exists():
                raise IOError(f"Path does not exist: {path}")
            elif not path.is_file():
                raise IOError(f"Path is not a file: {path}")

            expressions = _load_selection_expressions_from_file(path)
            frame_descriptors = self._get_descriptors(expressions)
        else:
            raise TypeError('frames has to be of type list, pathlib.Path or str')

        if shuffle:
            random.shuffle(frame_descriptors)

        return _FrameAccessor(self, frame_descriptors)


class _FrameAccessor:
    def __init__(self, loader: Loader, descriptors: Sequence[datatypes.Descriptor]):
        self._loader = loader
        self._descriptors = descriptors

    def _get_frame(self, descriptor: datatypes.Descriptor) -> datatypes.Frame:
        sequence_object = self._loader.get_frame_sequence(descriptor.frame_sequence)

        return sequence_object.get_frame(descriptor.frame)

    def __iter__(self):
        for descriptor in self._descriptors:
            yield self._get_frame(descriptor)

    def __len__(self):
        return len(self._descriptors)

    @functools.lru_cache()
    def __getitem__(self, index: int):
        if isinstance(index, int):
            if 0 <= index < len(self):
                return self._get_frame(self._descriptors[index])

            raise ValueError('index out of range')

        raise TypeError('item must be an int')
