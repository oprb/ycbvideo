import pytest

from ycbvideo import frame_access


def test_get_available_frame_sets_with_a_sequence_from_data(incomplete_dataset):
    # the frame sets 000001 - 000004 each miss at least one of the expected files
    # frame set 000005 is complete
    dataset = incomplete_dataset(missing_files={
        'data/0001': {'000001-color.png',
                      '000001-meta.mat',
                      '000002-depth.png',
                      '000003-label.png',
                      '000004-box.txt'}
    })

    sequence = frame_access.FrameSequence(dataset / 'data' / '0001')

    complete_frame_sets, incomplete_frame_sets = sequence.get_available_frame_sets()

    assert len(complete_frame_sets) == 1
    assert complete_frame_sets[0] == '000005'

    assert len(incomplete_frame_sets) == 4
    assert incomplete_frame_sets.keys() == {'000001', '000002', '000003', '000004'}

    assert 'color' in incomplete_frame_sets['000001']
    assert 'meta' in incomplete_frame_sets['000001']
    assert incomplete_frame_sets['000002'] == ['depth']
    assert incomplete_frame_sets['000003'] == ['label']
    assert incomplete_frame_sets['000004'] == ['box']


def test_get_available_frame_sets_with_data_syn_sequence(incomplete_dataset):
    # data_syn/ lacks any *-box.txt files, a frame set is therefore considered complete even if *-box.txt is missing

    # the frame sets 000001 - 000003 each miss at least one of the expected files
    # frame sets 000004 and 000005 are complete
    dataset = incomplete_dataset(missing_files={
        'data_syn': {'000001-color.png', '000001-meta.mat', '000002-depth.png', '000003-label.png'}
    })

    sequence = frame_access.FrameSequence(dataset / 'data_syn')

    complete_frame_sets, incomplete_frame_sets = sequence.get_available_frame_sets()

    assert len(complete_frame_sets) == 2
    assert '000004' in complete_frame_sets
    assert '000005' in complete_frame_sets

    assert len(incomplete_frame_sets) == 3
    assert incomplete_frame_sets.keys() == {'000001', '000002', '000003'}

    assert 'color' in incomplete_frame_sets['000001']
    assert 'meta' in incomplete_frame_sets['000001']
    assert incomplete_frame_sets['000002'] == ['depth']
    assert incomplete_frame_sets['000003'] == ['label']
    assert incomplete_frame_sets['000003'] == ['label']


def test_get_complete_frame_sets_with_a_sequence_from_data(incomplete_dataset):
    # the frame sets 000001 - 000004 each miss at least one of the expected files
    # frame set 000005 is complete
    dataset = incomplete_dataset(missing_files={
        'data/0001': {'000001-color.png', '000001-meta.mat', '000002-depth.png', '000003-label.png', '000004-box.txt'}
    })

    sequence = frame_access.FrameSequence(dataset / 'data' / '0001')

    frame_sets = sequence.get_complete_frame_sets()

    assert len(frame_sets) == 1
    assert frame_sets[0] == '000005'


def test_get_complete_frame_sets_with_data_syn_sequence(incomplete_dataset):
    # data_syn/ lacks any *-box.txt files, a frame set is therefore considered complete even if *-box.txt is missing

    # the frame sets 000001 - 000003 each miss at least one of the expected files
    # frame sets 000004 and 000005 are complete
    dataset = incomplete_dataset(missing_files={
        'data_syn': {'000001-color.png', '000001-meta.mat', '000002-depth.png', '000003-label.png'}
    })

    sequence = frame_access.FrameSequence(dataset / 'data_syn')

    frame_sets = sequence.get_complete_frame_sets()

    assert len(frame_sets) == 2
    assert '000004' in frame_sets
    assert '000005' in frame_sets


def test_get_incomplete_frame_sets_with_a_sequence_from_data(incomplete_dataset):
    # the frame sets 000001 - 000004 each miss at least one of the expected files
    # frame set 000005 is complete
    dataset = incomplete_dataset(missing_files={
        'data/0001': {'000001-color.png', '000001-meta.mat', '000002-depth.png', '000003-label.png', '000004-box.txt'}
    })

    sequence = frame_access.FrameSequence(dataset / 'data' / '0001')

    frame_sets = sequence.get_incomplete_frame_sets()

    assert len(frame_sets) == 4
    assert frame_sets.keys() == {'000001', '000002', '000003', '000004'}

    assert 'color' in frame_sets['000001']
    assert 'meta' in frame_sets['000001']
    assert frame_sets['000002'] == ['depth']
    assert frame_sets['000003'] == ['label']
    assert frame_sets['000004'] == ['box']


def test_get_incomplete_frame_sets_with_data_syn_sequence(incomplete_dataset):
    # data_syn/ lacks any *-box.txt files, a frame set is therefore considered complete even if *-box.txt is missing

    # the frame sets 000001 - 000003 each miss at least one of the expected files
    # frame sets 000004 and 000005 are complete
    dataset = incomplete_dataset(missing_files={
        'data_syn': {'000001-color.png', '000001-meta.mat', '000002-depth.png', '000003-label.png'}
    })

    sequence = frame_access.FrameSequence(dataset / 'data_syn')

    frame_sets = sequence.get_incomplete_frame_sets()

    assert len(frame_sets) == 3
    assert frame_sets.keys() == {'000001', '000002', '000003'}

    assert 'color' in frame_sets['000001']
    assert 'meta' in frame_sets['000001']
    assert frame_sets['000002'] == ['depth']
    assert frame_sets['000003'] == ['label']


@pytest.mark.parametrize('identifier', [138, '000138'])
def test_get_frame(dataset, identifier):
    # frame 0003/000138 is special in the sense that negative coordinates occur in 0003/000138-box.txt
    sequence = frame_access.FrameSequence(dataset / 'special_data' / '0003')

    frame = sequence.get_frame(identifier)

    assert frame.description == ('0003', '000138')
    assert frame.color is not None
    assert frame.depth is not None
    assert frame.label is not None
    assert frame.boxes is not None
    assert frame.meta is not None

    boxes = frame.boxes
    # compare every line with the corresponding box item
    with open('data/tests/ycb_video_dataset/special_data/0003/000138-box.txt', 'r') as f:
        for index, line in enumerate(f):
            box = boxes[index]
            x1, y1 = box.coordinates[0]
            x2, y2 = box.coordinates[1]
            # .2f is needed in case of trailing zeros, since the values in the *-box.txt files are stored with a
            # precision of 2 decimal digits
            assert f"{box.label} {x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f}\n" == line


def test_frames_info_with_no_missing_frames(dataset):
    info = frame_access.FrameAccessor(dataset).frames_info()
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

    info = frame_access.FrameAccessor(dataset).frames_info()
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


@pytest.mark.parametrize('description', [(0, 1),
                                         (0, '1'),
                                         ('0', 1),
                                         ('0', '1'),
                                         frame_access.Descriptor('0000', '000001')])
def test_frame_access_object_get_frame(dataset, description):
    frame = frame_access.FrameAccessObject(dataset, []).get_frame(description)

    assert frame.description == ('0000', '000001')

    boxes = frame.boxes
    # compare every line with the corresponding box item
    with open('data/tests/ycb_video_dataset/data/0000/000001-box.txt', 'r') as f:
        for index, line in enumerate(f):
            box = boxes[index]
            x1, y1 = box.coordinates[0]
            x2, y2 = box.coordinates[1]
            assert f"{box.label} {x1} {y1} {x2} {y2}\n" == line


def test_frame_access_object_supports_len_builtin(dataset):
    # the concrete descriptors do not matter
    descriptors = [frame_access.Descriptor('0001', '000001')] * 5

    frame_access_object = frame_access.FrameAccessObject(dataset, descriptors)

    assert hasattr(frame_access_object, '__len__')
    # test sequence 0001 contains 5 frames
    assert len(frame_access_object) == 5


def test_frame_access_object_supports_iter_builtin(dataset):
    descriptors = [frame_access.Descriptor('0001', '000001'),
                   frame_access.Descriptor('0001', '000002'),
                   frame_access.Descriptor('0001', '000003'),
                   frame_access.Descriptor('0001', '000004'),
                   frame_access.Descriptor('0001', '000005')]

    frame_access_object = frame_access.FrameAccessObject(dataset, descriptors)

    assert hasattr(frame_access_object, '__iter__')

    for frame, expected_descriptor in zip(
            iter(frame_access_object),
            [('0001', '000001'),
             ('0001', '000002'),
             ('0001', '000003'),
             ('0001', '000004'),
             ('0001', '000005')]):
        assert isinstance(frame, frame_access.Frame)
        assert frame.description == expected_descriptor


def test_frame_access_object_supports_get_item_builtin_given_ints(dataset):
    descriptors = [frame_access.Descriptor('0001', '000001'),
                   frame_access.Descriptor('0001', '000002'),
                   frame_access.Descriptor('0001', '000003'),
                   frame_access.Descriptor('0001', '000004'),
                   frame_access.Descriptor('0001', '000005')]

    frame_access_object = frame_access.FrameAccessObject(dataset, descriptors)

    assert hasattr(frame_access_object, '__getitem__')

    with pytest.raises(TypeError):
        # providing an on-the-fly created non-int object
        frame_access_object[type('not_an_int', (), {})]

    with pytest.raises(ValueError):
        # test sequence 0001 contains only 5 frames, 42 is sure out of range
        frame_access_object[42]

    for i, expected_descriptor in enumerate([('0001', '000001'),
                                             ('0001', '000002'),
                                             ('0001', '000003'),
                                             ('0001', '000004'),
                                             ('0001', '000005')]):
        frame = frame_access_object[i]
        assert isinstance(frame, frame_access.Frame)
        assert frame.description == expected_descriptor
