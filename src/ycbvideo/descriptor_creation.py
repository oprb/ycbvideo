from typing import List

from . import frame_access, parsing, selectors


class DescriptorCreator:
    def __init__(self, frame_accessor: frame_access.FrameAccessor):
        self._frame_accessor = frame_accessor

    def get_descriptors(self, expressions: List[str]) -> List[frame_access.Descriptor]:
        selectors = parsing.parse_selection_expressions(expressions)

        descriptors = []
        for selector in selectors:
            descriptors.extend(self._create_descriptors_from_selector(selector))

        return descriptors

    def _create_descriptors_from_selector(self, selector: selectors.Selector) -> List[frame_access.Descriptor]:
        available_sequences = sorted(self._frame_accessor.get_available_frame_sequences())

        descriptors = []
        try:
            selected_sequences = selector.select_sequences(available_sequences)
        except selectors.MissingElementError as error:
            raise IOError(f"Frame sequence is not available: {error.element}")

        for sequence in selected_sequences:
            sequence_object = self._frame_accessor.get_frame_sequence(sequence)

            complete_frames = sequence_object.get_complete_frame_sets()
            incomplete_frames = sequence_object.get_incomplete_frame_sets()
            # let the selector select from all frames available, even if some frames might be incomplete
            available_frames = sorted([*complete_frames, *incomplete_frames.keys()])

            try:
                selected_frames = selector.select_frames(available_frames)
            except selectors.MissingElementError as error:
                frame = error.element

                raise IOError(f"Frame is not available: {sequence}/{frame}")

            if selected_incomplete_frames := (set(selected_frames).difference(complete_frames)):
                incomplete_frame = list(selected_incomplete_frames)[0]
                missing_files = incomplete_frames[incomplete_frame]

                raise IOError(f"Files for frame missing: {sequence}/{incomplete_frame} misses {missing_files}")

            for frame in selected_frames:
                descriptors.append(frame_access.Descriptor(sequence, frame))

        return descriptors
