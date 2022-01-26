import pathlib

import pytest

from ycbvideo import utils


@pytest.mark.parametrize('type_', [pathlib.Path, str])
def test_validate_directory_path(type_, tmp_path):
    does_not_exist = tmp_path / 'does_not_exist'

    with pytest.raises(IOError):
        utils.validate_directory_path(type_(does_not_exist))

    is_a_file_not_a_directory = tmp_path / 'not_a_directory'
    is_a_file_not_a_directory.touch()

    with pytest.raises(IOError):
        utils.validate_directory_path(type_(is_a_file_not_a_directory))


def test_check_kind():
    # calling check_kind() with either 'sequence' or 'frame' should not raise an error
    utils.check_kind('sequence')
    utils.check_kind('frame')

    with pytest.raises(ValueError):
        utils.check_kind('neither_sequence_nor_frame')


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_normalize_element(kind):
    with pytest.raises(ValueError):
        utils.normalize_element('not_a_digit', kind)

    too_many_digits_element = {'sequence': '00042', 'frame': '0000042'}
    with pytest.raises(ValueError):
        utils.normalize_element(too_many_digits_element[kind], kind)

    expected_element = {'sequence': '0042', 'frame': '000042'}
    assert utils.normalize_element('42', kind) == expected_element[kind]


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_normalize_element(kind):
    with pytest.raises(ValueError):
        utils.normalize_optional_element('not_a_digit', kind)

    too_many_digits_element = {'sequence': '00042', 'frame': '0000042'}
    with pytest.raises(ValueError):
        utils.normalize_optional_element(too_many_digits_element[kind], kind)

    expected_element = {'sequence': '0042', 'frame': '000042'}
    assert utils.normalize_optional_element('42', kind) == expected_element[kind]

    assert utils.normalize_optional_element(None, kind) is None
