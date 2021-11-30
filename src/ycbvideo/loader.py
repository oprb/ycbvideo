import logging
import os
from pathlib import Path
import random
import re
from typing import List, Tuple, Iterable, Union, Iterator

from . import datatypes
from . import frameselection
from . import utils


class YcbVideoLoader:
    """

    """
    def __init__(self, path: Union[Path, str]):
        self._path = utils.validate_directory_path(path)
        self._data_directory = self._path / 'data'
        self._data_syn_directory = self._path / 'data_syn'
        self._available_data_frame_sequences = self.get_available_frame_sequences()
    """
        path: Path to the YCB-Video dataset root directory
    """

    def get_available_frame_sequences(self) -> List[str]:
        available_sequences = os.listdir(self._data_directory)

        if self._data_syn_directory.exists():
            available_sequences.append(self._data_syn_directory.name)

        return available_sequences

    def get_frame_sequence(self, index: Union[str, int]) -> datatypes.FrameSequence:
        if isinstance(index, int):
            index = "{:04d}".format(index)

        path = self._data_syn_directory if index == self._data_syn_directory.name else self._data_directory / index

        if index not in self.get_available_frame_sequences():
            raise IOError(f"Frame sequence does not exist: {index} ({path})")

        return datatypes.FrameSequence(path)

    def get_frame_sequences(self, indexes: Iterable[Union[int, str]]) -> List[datatypes.FrameSequence]:
        return [self.get_frame_sequence(index) for index in indexes]

    def get_frame(self, index: Union[str, Tuple[str, str]]) -> datatypes.Frame:
        if isinstance(index, str):
            if match := re.match(r'^(?P<framesequence>[0-9]{4}):(?P<frame>[0-9]{6})$', index):
                frame_sequence = match.group('framesequence')
                frame = match.group('frame')

                index = (frame_sequence, frame)
            else:
                raise ValueError(f"Invalid pattern (<frame_sequence>:<frame> required): {index}")

        return self.get_frame_sequence(index[0]).get_frame(index[1])

    def get_frame_descriptors(self, frame_selector: frameselection.FrameSelector) -> List[datatypes.FrameDescriptor]:
        frame_descriptors = []

        frame_sequence_selection = frameselection.get_items(frame_selector.frame_sequence_selection)
        frame_selection = frameselection.get_items(frame_selector.frame_selection)

        actual_frame_sequence_selection = None
        actual_frame_selection = None

        if frameselection.is_star_selection(frame_sequence_selection):
            actual_frame_sequence_selection = sorted(self._available_data_frame_sequences)
        else:
            actual_frame_sequence_selection = [frameselection.format_selection_item(frame_sequence, 'frame_sequence') for
                                               frame_sequence in frame_sequence_selection]
            for index, frame_sequence in enumerate(actual_frame_sequence_selection):
                if frame_sequence not in self._available_data_frame_sequences:
                    raise ValueError(
                        f"""Data Frame Sequence is not available: {frame_sequence}
                            (specified at index {index} in {frame_selector}""")

        for frame_sequence in actual_frame_sequence_selection:
            available_frames = sorted(self.get_frame_sequence(frame_sequence).get_available_frame_sets())

            if frameselection.is_star_selection(frame_selection):
                frame_descriptors.extend([datatypes.FrameDescriptor(frame_sequence, frame) for frame in available_frames])

                continue
            else:
                actual_frame_selection = [frameselection.format_selection_item(frame, 'frame') for
                                          frame in frame_selection]

            for index, frame in enumerate(actual_frame_selection):
                if frame not in available_frames:
                    raise ValueError(
                        f"""Data Frame is not available: {frame_sequence}:{frame}
                            (specified at index {index} in {frame_selector}""")

                frame_descriptors.append(datatypes.FrameDescriptor(frame_sequence, frame))

        return frame_descriptors

    def _get_frame(self, descriptor: datatypes.FrameDescriptor) -> datatypes.Frame:
        return self.get_frame_sequence(descriptor.frame_sequence).get_frame(descriptor.frame)

    def _get_descriptors_from_selections(self, selections: List[str]) -> List[datatypes.FrameDescriptor]:
        selectors = frameselection.get_frame_selectors(selections)

        return self._get_descriptors_from_selectors(selectors)

    def _get_descriptors_from_selectors(
            self,
            selectors: Iterable[frameselection.FrameSelector]) -> List[datatypes.FrameDescriptor]:
        frame_descriptors = []

        for selector in selectors:
            frame_descriptors.extend(self.get_frame_descriptors(selector))

        return frame_descriptors

    def frames(self, frames: Union[List[str], Union[Path, str]], shuffle: bool = False) -> Iterator[datatypes.Frame]:
        """
        Return an iterator for the specified frames.

        To be memory-friendly, the specified frames will be created
        just-in-time. The frames can be specified as either a list of
        selection expressions or as a path to a file with one selection
        expression per line.
        Frame sequences and frames can each be selected by an
        expression containing
            - a single element
            - a list of comma-delimited elements
            - a '*' expressing all available elements.
        Also, 'data_syn' can be used as a frame sequence selection
        element to specify the data_syn frame sequence.
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
            - '[data_syn,2,1]:*'
                Get all available frames from the data_syn, 2nd and 1st
                frame sequence each

        If `shuffle` is set to 'False', the frames will be returned
        in exactly the order as specified by the order of selection
        expressions and the order of the elements in those. Otherwise,
        the frames get shuffled. Because random.shuffle() is used to
        shuffle the frames, by setting a seed with random.seed(), the
        frames will be shuffled the same way each time this method is
        called.

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

        Yields
        ------
        Frame
            A frame specified by frames
        """

        if isinstance(frames, list):
            frame_descriptors = self._get_descriptors_from_selections(frames)
        elif isinstance(frames, (Path, str)):
            path = Path(frames)

            if not path.is_absolute():
                path = self._path / path

            frame_selectors = frameselection.load_frame_selectors_from_file(path)
            frame_descriptors = self._get_descriptors_from_selectors(frame_selectors)
        else:
            raise TypeError('frames has to be of type list, pathlib.Path or str')

        if shuffle:
            random.shuffle(frame_descriptors)

        for descriptor in frame_descriptors:
            yield self._get_frame(descriptor)
