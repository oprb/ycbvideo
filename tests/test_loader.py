from pathlib import Path
import shutil
from typing import Iterator, Union, List, Type

import pytest

import ycbvideo.datatypes
from ycbvideo.loader import YcbVideoLoader


@pytest.fixture()
def loader(dataset):
    return YcbVideoLoader(dataset)


def check_frame_items(frames: Iterator[ycbvideo.datatypes.Frame]):
    frame_items = [frame for frame in frames]

    # expected are 5 frames from sequence 0001, three from sequence 0002 and one frame from data_syn
    assert len(frame_items) == 5 + 3 + 1

    expected_descriptors = [
        ('0001', '000001'),
        ('0001', '000002'),
        ('0001', '000003'),
        ('0001', '000004'),
        ('0001', '000005'),
        ('0002', '000002'),
        ('0002', '000003'),
        ('0002', '000005'),
        ('data_syn', '000001')
    ]
    for item in zip(frame_items, expected_descriptors):
        frame_item, expected_descriptor = item

        assert frame_item.description == expected_descriptor

    for index, frame in enumerate(frame_items):
        assert frame.color is not None
        assert frame.depth is not None
        assert frame.label is not None

        assert frame.boxes is not None if frame.description.frame_sequence != 'data_syn' else frame.boxes is None


def check_for_immediate_error(loader: YcbVideoLoader,
                              selection: Union[List[str], Union[Path, str]],
                              error: Type[Exception]):
    with pytest.raises(error):
        next(loader.frames(selection))


def test_select_frames_from_selection(loader):
    check_frame_items(loader.frames(['1/*', '2/[2,3,5]', 'data_syn/000001']))


def test_select_frames_from_file_with_absolut_path(loader):
    file = Path('data/tests/selections.txt').resolve()

    check_frame_items(loader.frames(file))


def test_select_frames_from_file_with_relative_path(dataset):
    file = 'selections.txt'
    image_sets = 'image_sets'
    (dataset / image_sets).mkdir()

    shutil.copy('data/tests/selections.txt', dataset / image_sets / file)
    loader = YcbVideoLoader(dataset)

    check_frame_items(loader.frames(f"{image_sets}/{file}"))


def test_frames_with_path_given_as_str(loader):
    file = Path('data/tests/selections.txt').resolve()

    # with path given as pathlib.Path object
    check_frame_items(loader.frames(str(file)))


def test_frames_with_invalid_selection(loader):
    # make sure an error is raised already when the first frame
    # is requested from the iterator even if the invalid expression
    # is not specified first
    check_for_immediate_error(loader, ['1/*', '2/[*]', 'data_syn/000001'], ValueError)


def test_frames_with_missing_files(incomplete_dataset):
    dataset = incomplete_dataset(missing_files={
        'data/0001': {'000002-color.png', '000003-depth.png', '000004-label.png', '000005-box.txt'},
        'data/0002': {'000002-depth.png', '000002-label.png'},
        'data_syn': {'000002-meta.mat'}
    })

    loader = YcbVideoLoader(dataset)

    # make sure an error is raised already when the first frame
    # is requested from the iterator even if the expression
    # specifying the missing element is not specified first

    # color image is missing
    check_for_immediate_error(loader, ['1/1', '1/2'], IOError)

    # depth image is missing
    check_for_immediate_error(loader, ['1/1', '1/3'], IOError)

    # label image is missing
    check_for_immediate_error(loader, ['1/1', '1/4'], IOError)

    # box file is missing
    check_for_immediate_error(loader, ['1/1', '1/5'], IOError)

    # both depth and label images are missing
    check_for_immediate_error(loader, ['2/1', '2/2'], IOError)

    # meta.mat files are not required and can be missing
    frame = next(loader.frames(['data_syn/2']))
    assert frame.description == ycbvideo.datatypes.FrameDescriptor('data_syn', '000002')
    assert frame.color is not None
    assert frame.depth is not None
    assert frame.label is not None
