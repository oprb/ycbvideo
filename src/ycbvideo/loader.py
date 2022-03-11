from pathlib import Path
from typing import List, Iterable, Union

from . import frame_access, descriptor_creation, utils


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


def _get_expressions_from_source(dataset_path: Union[Path, str],
                                 source: Union[List[str], Union[Path, str]]) -> List[str]:
    if not isinstance(dataset_path, (Path, str)):
        raise TypeError('root_path must either be a pathlib.Path or a str')

    dataset_path = Path(dataset_path)

    if isinstance(source, list):
        if not source:
            raise ValueError('List is empty')

        return source
    elif isinstance(source, (Path, str)):
        path = Path(source)

        if not path.is_absolute():
            path = dataset_path / path

        if not path.exists():
            raise IOError(f"Path does not exist: {path}")
        elif not path.is_file():
            raise IOError(f"Path is not a file: {path}")

        return _load_selection_expressions_from_file(path)

    raise TypeError('source has to be a list, a pathlib.Path or a str')


class Loader:
    def __init__(self, path: Union[Path, str]):
        self._path = utils.validate_directory_path(path)
        self._frame_accessor = frame_access.FrameAccessor(self._path)
        self._descriptor_creator = descriptor_creation.DescriptorCreator(self._frame_accessor)

    def frames(self,
               frames: Union[List[str], Union[Path, str]],
               shuffle: bool = False) -> frame_access.FrameAccessObject:
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
        FrameAccessObject
            An object allowing access to the frame objects,
            supporting iteration (__iter__()), determining
            the number of frames selected (__len__()),
            direct access (__getitem__()) but also access
            to the underlying frame descriptors, if necessary.
        """

        expressions = _get_expressions_from_source(self._path, frames)
        descriptors = self._descriptor_creator.get_descriptors(expressions)

        frame_access_object = frame_access.FrameAccessObject(self._path, descriptors)

        if shuffle:
            frame_access_object.shuffle()

        return frame_access_object
