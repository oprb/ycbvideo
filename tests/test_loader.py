import random
from pathlib import Path
import shutil
from typing import Union, List, Type, Tuple, Iterable

import pytest

import ycbvideo.datatypes
from ycbvideo.loader import Loader


@pytest.fixture()
def loader(dataset):
    return Loader(dataset)


def check_frame_items(frames: Iterable[ycbvideo.datatypes.Frame]):
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

    check_descriptors(frames, expected_descriptors)

    for index, frame in enumerate(frame_items):
        assert frame.color is not None
        assert frame.depth is not None
        assert frame.label is not None
        assert frame.meta is not None

        assert frame.boxes is not None if frame.description.frame_sequence != 'data_syn' else frame.boxes is None


def check_descriptors(frames: Iterable[ycbvideo.datatypes.Frame], expected_descriptions: List[Tuple[str, str]]):
    frame_items = list(frames)

    for frame, expected_description in zip(frame_items, expected_descriptions):
        assert frame.description == expected_description


def check_for_immediate_error(loader: Loader,
                              selection: Union[List[str], Union[Path, str]],
                              error: Type[Exception]):
    with pytest.raises(error):
        loader.frames(selection)


def test_frames_supports_len_builtin(loader):
    frames = loader.frames(['1/*'])

    assert hasattr(frames, '__len__')
    # test sequence 0001 contains 5 frames
    assert len(frames) == 5


def test_frames_supports_iter_builtin(loader):
    frames = loader.frames(['1/*'])

    assert hasattr(frames, '__iter__')

    for frame, expected_descriptor in zip(
            iter(frames),
            [('0001', '000001'),
             ('0001', '000002'),
             ('0001', '000003'),
             ('0001', '000004'),
             ('0001', '000005')]):
        assert isinstance(frame, ycbvideo.datatypes.Frame)
        assert frame.description == expected_descriptor


def test_frames_supports_get_item_builtin_given_ints(loader):
    frames = loader.frames(['1/*'])

    assert hasattr(frames, '__getitem__')

    with pytest.raises(TypeError):
        # providing an on-the-fly created non-int object
        frames[type('not_an_int', (), {})]

    with pytest.raises(ValueError):
        # test sequence 0001 contains only 5 frames, 42 is sure out of range
        frames[42]

    for i, expected_descriptor in enumerate([('0001', '000001'),
                                             ('0001', '000002'),
                                             ('0001', '000003'),
                                             ('0001', '000004'),
                                             ('0001', '000005')]):
        frame = frames[i]
        assert isinstance(frame, ycbvideo.datatypes.Frame)
        assert frame.description == expected_descriptor


def test_frames_with_sequence_0000(loader):
    # make sure that there is no confusion that frame sequences start with index '0000'
    # but frames with index '000001'
    frame = next(iter(loader.frames(['0/1'])))

    assert frame.description == ('0000', '000001')

    boxes = frame.boxes
    # compare every line with the corresponding box item
    with open('data/tests/ycb_video_dataset/data/0000/000001-box.txt', 'r') as f:
        for index, line in enumerate(f):
            box = boxes[index]
            x1, y1 = box.coordinates[0]
            x2, y2 = box.coordinates[1]
            assert f"{box.label} {x1} {y1} {x2} {y2}\n" == line


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
    loader = Loader(dataset)

    check_frame_items(loader.frames(f"{image_sets}/{file}"))


def test_frames_with_path_given_as_str(loader):
    file = Path('data/tests/selections.txt').resolve()

    # with path given as pathlib.Path object
    check_frame_items(loader.frames(str(file)))


def test_frames_with_data_specified(loader):
    # with a single frame
    check_descriptors(
        loader.frames(['data/2']),
        [('0000', '000002'),
         ('0001', '000002'),
         ('0002', '000002')]
    )

    # with a list of frames
    check_descriptors(
        loader.frames(['data/[1,4]']),
        [('0000', '000001'),
         ('0000', '000004'),
         ('0001', '000001'),
         ('0001', '000004'),
         ('0002', '000001'),
         ('0002', '000004')]
    )

    # with star expression
    check_descriptors(
        loader.frames(['data/*']),
        [('0000', '000001'),
         ('0000', '000002'),
         ('0000', '000003'),
         ('0000', '000004'),
         ('0000', '000005'),
         ('0001', '000001'),
         ('0001', '000002'),
         ('0001', '000003'),
         ('0001', '000004'),
         ('0001', '000005'),
         ('0002', '000001'),
         ('0002', '000002'),
         ('0002', '000003'),
         ('0002', '000004'),
         ('0002', '000005')]
    )


def test_frames_with_invalid_selection(loader):
    # make sure an error is raised already when the first frame
    # is requested from the iterator even if the invalid expression
    # is not specified first
    check_for_immediate_error(loader, ['1/*', '2/[*]', 'data_syn/000001'], ValueError)


def test_frames_with_request_for_missing_frame_sequence(loader):
    # the test dataset does not contain a data/0003 directory
    # make sure an error is raised already when the first frame
    # is requested from the iterator even if the missing frame
    # sequence is not specified first
    check_for_immediate_error(loader, ['1/*', '3/1'], IOError)


def test_frames_with_missing_files(incomplete_dataset):
    dataset = incomplete_dataset(missing_files={
        'data/0001': {'000002-color.png', '000003-depth.png', '000004-label.png', '000005-box.txt'},
        'data/0002': {'000002-depth.png', '000002-label.png'},
        'data_syn': {'000002-meta.mat'}
    })

    loader = Loader(dataset)

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

    # meta.mat file is missing
    check_for_immediate_error(loader, ['data_syn/2'], IOError)


def test_frames_info_with_no_missing_frames(loader):
    info = loader.frames_info()
    found_sequences = info.keys()

    assert len(found_sequences) == 4

    for sequence in found_sequences:
        found_frame_sets = info[sequence]

        assert len(found_frame_sets) == 5
        # make sure there is no list of missing items for any of the found frame sets
        assert all(map(lambda missing_items: missing_items is None, found_frame_sets.values()))


def test_frames_info_with_missing_frames(incomplete_dataset):
    dataset = incomplete_dataset(missing_files={
        'data/0001': {'000002-color.png', '000005-box.txt'},
        'data/0002': {'000002-depth.png', '000002-label.png'},
        'data_syn': {'000002-meta.mat', '000004-label.png'}
    })

    loader = Loader(dataset)
    info = loader.frames_info()
    expected_info = {
        '0000': {
            '000001': None,
            '000002': None,
            '000003': None,
            '000004': None,
            '000005': None
        },
        '0001': {
            '000001': None,
            '000002': ['color'],
            '000003': None,
            '000004': None,
            '000005': ['box']
        },
        '0002': {
            '000001': None,
            '000002': ['depth', 'label'],
            '000003': None,
            '000004': None,
            '000005': None
        },
        'data_syn': {
            '000001': None,
            '000002': ['meta'],
            '000003': None,
            '000004': ['label'],
            '000005': None
        }
    }

    # entries have to be the same, not the order
    assert info == expected_info


def test_frames_with_valid_range_expressions(loader):
    frames = list(loader.frames(['0:1/5::-2', 'data_syn/4::-1']))

    assert len(frames) == 7

    expected_descriptors = [
        ('0000', '000005'),
        ('0000', '000003'),
        ('0000', '000001'),
        ('data_syn', '000004'),
        ('data_syn', '000003'),
        ('data_syn', '000002'),
        ('data_syn', '000001'),
    ]

    check_descriptors(frames, expected_descriptors)


def test_frames_with_range_expressions_and_missing_frames(incomplete_dataset):
    dataset = incomplete_dataset(missing_files={
        'data/0001': {'000003-color.png', '000003-depth.png', '000003-label.png', '000003-box.txt', '000003-meta.mat'}
    })

    frames = list(Loader(dataset).frames(['1/:']))

    assert len(frames) == 4

    expected_descriptors = [
        ('0001', '000001'),
        ('0001', '000002'),
        ('0001', '000004'),
        ('0001', '000005'),
    ]

    check_descriptors(frames, expected_descriptors)


def test_frames_with_range_expressions_and_missing_sequences(dataset):
    shutil.rmtree(dataset / 'data' / '0001')

    frames = list(Loader(dataset).frames([':/1']))

    assert len(frames) == 2

    expected_descriptors = [
        ('0000', '000001'),
        ('0002', '000001'),
    ]

    check_descriptors(frames, expected_descriptors)


def test_frames_with_range_expressions_and_incomplete_frames(incomplete_dataset):
    dataset = incomplete_dataset(missing_files={
        'data/0000': {'000003-meta.mat'},
        'data/0001': {'000003-color.png', '000005-depth.png'},
        'data/0002': {'000003-label.png', '000005-box.txt'}
    })

    loader = Loader(dataset)

    # incomplete frame 000003 included in range
    check_for_immediate_error(loader, ['0/:'], IOError)
    # incomplete frame 000003 as start
    check_for_immediate_error(loader, ['0/3:'], IOError)

    # incomplete frame 000003 included in range
    check_for_immediate_error(loader, ['1/:4'], IOError)
    # incomplete frame 000003 as start
    check_for_immediate_error(loader, ['1/3:'], IOError)
    # incomplete frame 000005 as implicit range stop
    check_for_immediate_error(loader, ['1/4:'], IOError)
    # incomplete frame 000003 included in range
    check_for_immediate_error(loader, ['2/:4'], IOError)
    # incomplete frame 000003 as start
    check_for_immediate_error(loader, ['2/3:'], IOError)
    # incomplete frame 000005 as implicit range stop
    check_for_immediate_error(loader, ['2/4:'], IOError)


def test_frames_with_missing_frames_specified_as_start_or_stop_in_range_expression(incomplete_dataset):
    dataset = incomplete_dataset(missing_files={
        'data/0001': {'000003-color.png', '000003-depth.png', '000003-label.png', '000003-box.txt', '000003-meta.mat'}
    })

    loader = Loader(dataset)

    # missing frame specified as start
    check_for_immediate_error(loader, ['1/3:'], IOError)

    # missing frame specified as stop
    check_for_immediate_error(loader, ['1/:3'], IOError)


def test_frames_with_missing_sequences_specified_as_start_or_stop_in_range_expression(loader):
    # the test data only contains frames from the sequences 0000, 0001, 0002, data_syn, not 0042

    # missing sequence specified as start
    check_for_immediate_error(loader, ['0042:/:'], IOError)

    # missing sequence specified as stop
    check_for_immediate_error(loader, [':0042/:'], IOError)


def test_frames_with_start_equals_stop_in_range_expression(loader):
    # since an empty selection is of no use, an exception is thrown
    # but the type of exception does not really matter

    # when selecting frame sequences
    check_for_immediate_error(loader, ['0000:0000/2'], Exception)

    # when selecting frames
    check_for_immediate_error(loader, ['0000/2:2'], Exception)


def test_frames_with_step_size_of_zero(loader):
    # the type of exception does not really matter

    # in a frame sequence selection and with '0'
    check_for_immediate_error(loader, ['::0/1'], Exception)

    # in a frame sequence selection and with '-0'
    check_for_immediate_error(loader, ['::-0/1'], Exception)

    # in a frame selection and with '0'
    check_for_immediate_error(loader, ['1/::0'], Exception)

    # in a frame selection and with '-0'
    check_for_immediate_error(loader, ['1/::-0'], Exception)


def test_frames_with_negative_start_or_stop(loader):
    # the type of exception does not really matter

    # frame sequence selection with negative start
    check_for_immediate_error(loader, ['-1:/1'], Exception)

    # frame sequence selection with negative stop
    check_for_immediate_error(loader, [':-1/1'], Exception)

    # frame selection with negative start
    check_for_immediate_error(loader, ['1/-1:'], Exception)

    # frame selection with negative stop
    check_for_immediate_error(loader, ['1/:-1'], Exception)


def test_frames_with_empty_expression_list(loader):
    check_for_immediate_error(loader, [], ValueError)


def test_frames_with_path_pointing_to_a_directory_instead_of_a_file(dataset, tmp_path):
    loader = Loader(dataset)

    path_to_a_directory = tmp_path / 'not_a_file'
    path_to_a_directory.mkdir()

    check_for_immediate_error(loader, path_to_a_directory, IOError)


def test_frames_with_none_given_as_path(loader):
    check_for_immediate_error(loader, None, TypeError)


def test_frames_are_shuffled_as_set_by_seed(loader):
    random.seed(42)
    first_run = [frame.description for frame in loader.frames(['*/*'], shuffle=True)]

    random.seed(42)
    second_run =[frame.description for frame in loader.frames(['*/*'], shuffle=True)]

    assert first_run == second_run


def test_frames_are_shuffled_the_same_when_state_is_reset(loader):
    random.seed(42)
    state = random.getstate()
    first_run = [frame.description for frame in loader.frames(['*/*'], shuffle=True)]

    random.setstate(state)
    second_run = [frame.description for frame in loader.frames(['*/*'], shuffle=True)]

    assert first_run == second_run
