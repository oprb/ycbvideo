import pytest

from ycbvideo import info


def check_consecution(item1: int, item2: int) -> bool:
    return item2 == item1 + 1


def check_string_consecution(item1: str, item2: str) -> bool:
    if item1.isdigit() and item2.isdigit():
        return check_consecution(int(item1), int(item2))

    return False


def test_get_item_ranges():
    # test with zero items
    assert info.get_item_ranges([], check_consecution=check_consecution) == []

    # test with single item
    assert info.get_item_ranges([42], check_consecution=check_consecution) == [(0, 1)]

    # test with a range of consecutive items
    assert info.get_item_ranges([42, 43, 44, 45, 46], check_consecution=check_consecution) == [(0, 5)]

    # test with ranges and single items
    assert info.get_item_ranges([0, 7, 8, 13, 42, 43, 44, 49], check_consecution=check_consecution) \
           == [(0, 1), (1, 3), (3, 4), (4, 7), (7, 8)]
    assert info.get_item_ranges([7, 8, 0, 42, 43, 44, 13, 49], check_consecution=check_consecution) \
           == [(0, 2), (2, 3), (3, 6), (6, 7), (7, 8)]


def test_format_in_ranges():
    # test with zero items
    assert info.format_in_ranges([], check_consecution=check_string_consecution) == []

    # test with single item
    assert info.format_in_ranges(['0042'], check_consecution=check_string_consecution) == ['0042']

    # test with a range of consecutive items
    assert info.format_in_ranges(['0042', '0043', '0044'], check_consecution=check_string_consecution)\
           == ['0042 - 0044']

    # test with ranges and single items
    assert info.format_in_ranges(
               ['0000', '0007', '0008', '0013', '0042', '0043', '0044', '0049', 'data_syn'],
               check_consecution=check_string_consecution)\
           == ['0000', '0007 - 0008', '0013', '0042 - 0044', '0049', 'data_syn']
