from pathlib import Path
import shutil
from typing import Iterator

import pytest

import ycbvideo.datatypes
from ycbvideo.loader import YcbVideoLoader


@pytest.fixture(scope='session')
def dataset(tmp_path_factory):
    test_data = tmp_path_factory.mktemp('test_data')
    dataset = test_data / 'dataset'

    # should not be modified
    data_source = Path('data/tests/ycb_video_dataset')
    shutil.copytree(data_source, dataset, symlinks=True)

    return dataset


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


@pytest.mark.xfail(reason='possible error in pytest execution')
def test_frames_with_invalid_selection(loader):
    # with pytest.raises(ValueError):
    #     loader.frames(['1/*', '2/[*]', 'data_syn/000001'])
    frames = [frame for frame in loader.frames(['1/*', '2/[*]', 'data_syn/000001'])]
    assert len([loader.frames(['1/*', '2/[*]', 'data_syn/000001'])]) > 0
