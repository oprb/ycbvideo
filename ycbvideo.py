import os
import re
import logging
from typing import List, Tuple, Iterable, Union
import datatypes
import frameselection


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

    def get_frame_sequence(self, index: Union[str, int]) -> datatypes.FrameSequence:
        if isinstance(index, int):
            index = "{:04d}".format(index)
        if index not in self.get_available_frame_sequences():
            raise IOError(f"Data sequence does not exist: {index} ({self._path}/{self._data_directory}/{index})")

        return datatypes.FrameSequence(f"{self._path}/{self._data_directory}/{index}")

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
            available_frames = sorted(self.get_available_frames(frame_sequence))

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
        frame_descriptors = []

        for selector in frameselection.get_frame_selectors(selections):
            frame_descriptors.extend(self.get_frame_descriptors(selector))

        return frame_descriptors

    def frames(self, frames: List[str]) -> Iterable[datatypes.Frame]:
        frame_descriptors = self._get_descriptors_from_selections(frames)

        for descriptor in frame_descriptors:
            yield self._get_frame(descriptor)
