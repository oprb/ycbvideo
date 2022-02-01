import pytest

from ycbvideo import datatypes


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

    sequence = datatypes.FrameSequence(dataset / 'data' / '0001')

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

    sequence = datatypes.FrameSequence(dataset / 'data_syn')

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

    sequence = datatypes.FrameSequence(dataset / 'data' / '0001')

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

    sequence = datatypes.FrameSequence(dataset / 'data_syn')

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

    sequence = datatypes.FrameSequence(dataset / 'data' / '0001')

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

    sequence = datatypes.FrameSequence(dataset / 'data_syn')

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
    sequence = datatypes.FrameSequence(dataset / 'special_data' / '0003')

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
