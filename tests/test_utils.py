import pytest

from ycbvideo.utils import expand_range, RangeError, MissingItemError

ITEMS = ['40', '41', '42', '43', '44', '47', '55', '56']


def test_expand_range_with_positive_step_size():
    # start given
    assert expand_range(('42', None, None), ITEMS) == ['42', '43', '44', '47', '55', '56']
    # start and stop given
    assert expand_range(('42', '55', None), ITEMS) == ['42', '43', '44', '47']
    # start and step given
    assert expand_range(('42', None, 2), ITEMS) == ['42', '44', '55']
    # start, stop and step given
    assert expand_range(('42', '55', 2), ITEMS) == ['42', '44']
    # stop given
    assert expand_range((None, '55', None), ITEMS) == ['40', '41', '42', '43', '44', '47']
    # stop and step given
    assert expand_range((None, '55', 2), ITEMS) == ['40', '42', '44']
    # step given
    assert expand_range((None, None, 2), ITEMS) == ['40', '42', '44', '55']
    # start equals first item
    assert expand_range(('40', None, None), ITEMS) == ['40', '41', '42', '43', '44', '47', '55', '56']
    # stop equals last item
    assert expand_range((None, '56', None), ITEMS) == ['40', '41', '42', '43', '44', '47', '55']
    # stop is start's successor
    assert expand_range(('42', '43', None), ITEMS) == ['42']


def test_expand_range_with_negative_step_size():
    # start given
    assert expand_range(('55', None, -1), ITEMS) == ['55', '47', '44', '43', '42', '41', '40']
    # start and stop given
    assert expand_range(('55', '42', -1), ITEMS) == ['55', '47', '44', '43']
    # greater negative step size
    assert expand_range(('55', '42', -2), ITEMS) == ['55', '44']
    # stop given
    assert expand_range((None, '42', -1), ITEMS) == ['56', '55', '47', '44', '43']
    # step given
    assert expand_range((None, None, -1), ITEMS) == ['56', '55', '47', '44', '43', '42', '41', '40']
    # start equals last item
    assert expand_range(('56', None, -1), ITEMS) == ['56', '55', '47', '44', '43', '42', '41', '40']
    # stop equals first item
    assert expand_range((None, '40', -1), ITEMS) == ['56', '55', '47', '44', '43', '42', '41']
    # stop is start's predecessor
    assert expand_range(('42', '41', -1), ITEMS) == ['42']


def test_expand_range_with_no_items():
    with pytest.raises(RangeError):
        assert expand_range((None, None, None), [])


def test_expand_range_with_step_size_of_zero():
    with pytest.raises(RangeError):
        assert expand_range((None, None, 0), ITEMS)


def test_expand_range_with_invalid_ranges():
    # start is greater than stop
    with pytest.raises(RangeError):
        assert expand_range(('55', '42', None), ITEMS)

    # stop is greater than start
    with pytest.raises(RangeError):
        assert expand_range(('42', '55', -1), ITEMS)

    # stop equals start
    with pytest.raises(RangeError):
        assert expand_range(('42', '42', None), ITEMS)


def test_expand_range_with_missing_items():
    # item specified as start is missing in items
    with pytest.raises(MissingItemError) as exception_info:
        expand_range(('39', '55', None), ITEMS)

    error = exception_info.value
    assert error.item == '39'
    assert error.usage == 'start'

    # item specified as stop is missing in items
    with pytest.raises(MissingItemError) as exception_info:
        expand_range((None, '57', None), ITEMS)

    error = exception_info.value
    assert error.item == '57'
    assert error.usage == 'stop'
