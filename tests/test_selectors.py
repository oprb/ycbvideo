from typing import Callable, List, Union

import pytest

from ycbvideo import selectors
from ycbvideo.selectors import ListSelector, RangeSelector, SingleElementSelector, StarSelector
from ycbvideo.selectors import DataSelector, DataSynSelector
from ycbvideo.selectors import EmptySelectionError, MissingElementError

ELEMENTS = [40, 41, 42, 43, 44, 47, 55, 56]


def format_as(item: Union[int, List[int]], kind: str) -> Union[str, List[str]]:
    """Normalize a single integer or a list of integers """
    def _normalize_element(element: int, kind: str) -> str:
        if kind == 'sequence':
            return "{:04d}".format(element)
        elif kind == 'frame':
            return "{:06d}".format(element)

        raise ValueError(f"kind must be 'sequence' or 'frame': {kind}")

    if isinstance(item, int):
        return _normalize_element(item, kind)
    elif isinstance(item, list):
        return [_normalize_element(element, kind) for element in item]


def get_formatter(kind: str) -> Callable[[Union[int, List[int]]], Union[str, List[str]]]:
    return lambda item: format_as(item, kind)


def select_and_compare(
        selector: selectors.ElementSelector,
        given_elements: List[str],
        expected_selection: List[str]):

    assert selector.select(given_elements) == expected_selection


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_single_element_select(kind):
    _format = get_formatter(kind)
    elements = _format(ELEMENTS)

    # first element in elements
    select_and_compare(
        SingleElementSelector('40', _format(40)),
        given_elements=elements,
        expected_selection=_format([40])
    )

    # element in the middle of elements
    select_and_compare(
        SingleElementSelector('47', _format(47)),
        given_elements=elements,
        expected_selection=_format([47])
    )

    # last element in elements
    select_and_compare(
        SingleElementSelector('56', _format(56)),
        given_elements=elements,
        expected_selection=_format([56])
    )


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_single_element_select_with_missing_element(kind):
    _format = get_formatter(kind)
    element = _format(13)
    elements = _format(ELEMENTS)

    with pytest.raises(MissingElementError) as exception_info:
        SingleElementSelector('13', element).select(elements)

    error = exception_info.value
    assert error.element == element
    assert error.elements == elements


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_list_select_with_multiple_elements(kind):
    _format = get_formatter(kind)
    elements_to_select = _format([40, 47, 56])
    elements = _format(ELEMENTS)

    select_and_compare(
        ListSelector('[40,47,56]', elements_to_select),
        given_elements=elements,
        expected_selection=elements_to_select
    )


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_list_select_with_single_element(kind):
    _format = get_formatter(kind)
    elements = _format(ELEMENTS)

    select_and_compare(
        ListSelector('[42]', _format([42])),
        given_elements=elements,
        expected_selection=_format([42])
    )


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_list_select_with_missing_element(kind):
    _format = get_formatter(kind)
    elements = _format(ELEMENTS)

    # element 13 is missing
    with pytest.raises(MissingElementError) as exception_info:
        ListSelector('[42,13,47]', _format([42, 13, 47])).select(elements)

    error = exception_info.value
    assert error.element == _format(13)
    assert error.elements == elements


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_star_select(kind):
    _format = get_formatter(kind)
    elements = _format(ELEMENTS)

    select_and_compare(
        StarSelector(),
        given_elements=elements,
        expected_selection=elements
    )


def test_data_select():
    elements = format_as(ELEMENTS, 'sequence')
    elements_with_data_syn_sequence = [*elements, 'data_syn']

    select_and_compare(
        DataSelector(),
        given_elements=elements_with_data_syn_sequence,
        expected_selection=elements
    )


def test_data_syn_select():
    elements = format_as(ELEMENTS, 'sequence')
    elements_with_data_syn_sequence = [*elements, 'data_syn']

    select_and_compare(
        DataSynSelector(),
        given_elements=elements_with_data_syn_sequence,
        expected_selection=['data_syn']
    )


def test_data_syn_select_with_data_syn_missing():
    elements = format_as(ELEMENTS, 'sequence')

    with pytest.raises(MissingElementError) as exception_info:
        DataSynSelector().select(elements)

    error = exception_info.value
    assert error.element == 'data_syn'
    assert error.elements == elements


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_range_select_with_positive_step_size(kind):
    _format = get_formatter(kind)
    elements = _format(ELEMENTS)

    # start given
    select_and_compare(
        RangeSelector('42:', _format(42), None),
        given_elements=elements,
        expected_selection=_format([42, 43, 44, 47, 55, 56]))

    # start and stop given
    select_and_compare(
        RangeSelector('42:55', _format(42), _format(55)),
        given_elements=elements,
        expected_selection=_format([42, 43, 44, 47]))

    # start and step given
    select_and_compare(
        RangeSelector('42::2', _format(42), None, 2),
        given_elements=elements,
        expected_selection=_format([42, 44, 55])
    )

    # start, stop and step given
    select_and_compare(
        RangeSelector('42:55:2', _format(42), _format(55), 2),
        given_elements=elements,
        expected_selection=_format([42, 44])
    )

    # stop given
    select_and_compare(
        RangeSelector(':55', None, _format(55)),
        given_elements=elements,
        expected_selection=_format([40, 41, 42, 43, 44, 47])
    )

    # stop and step given
    select_and_compare(
        RangeSelector(':55:2', None, _format(55), 2),
        given_elements=elements,
        expected_selection=_format([40, 42, 44])
    )

    # step given
    select_and_compare(
        RangeSelector('::2', None, None, 2),
        given_elements=elements,
        expected_selection=_format([40, 42, 44, 55])
    )

    # start equals first item
    select_and_compare(
        RangeSelector('40:', _format(40), None),
        given_elements=elements,
        expected_selection=_format([40, 41, 42, 43, 44, 47, 55, 56])
    )

    # stop equals last item
    select_and_compare(
        RangeSelector(':56', None, _format(56)),
        given_elements=elements,
        expected_selection=_format([40, 41, 42, 43, 44, 47, 55])
    )

    # stop is start's successor
    select_and_compare(
        RangeSelector('42:43', _format(42), _format(43)),
        given_elements=elements,
        expected_selection=[_format(42)]
    )


@pytest.mark.parametrize('kind', ['frame', 'sequence'])
def test_range_select_with_negative_step_size(kind):
    _format = get_formatter(kind)
    elements = _format(ELEMENTS)

    # start given
    select_and_compare(
        RangeSelector('55::-1', _format(55), None, -1),
        given_elements=elements,
        expected_selection=_format([55, 47, 44, 43, 42, 41, 40])
    )

    # start and stop given
    select_and_compare(
        RangeSelector('55:42:-1', _format(55), _format(42), -1),
        given_elements=elements,
        expected_selection=_format([55, 47, 44, 43])
    )

    # greater negative step size
    select_and_compare(
        RangeSelector('55:42:-2', _format(55), _format(42), -2),
        given_elements=elements,
        expected_selection=_format([55, 44])
    )

    # stop given
    select_and_compare(
        RangeSelector(':42:-1', None, _format(42), -1),
        given_elements=elements,
        expected_selection=_format([56, 55, 47, 44, 43])
    )

    # step given
    select_and_compare(
        RangeSelector('::-1', None, None, -1),
        given_elements=elements,
        expected_selection=_format([56, 55, 47, 44, 43, 42, 41, 40])
    )

    # start equals last item
    select_and_compare(
        RangeSelector('56::-1', _format(56), None, -1),
        given_elements=elements,
        expected_selection=_format([56, 55, 47, 44, 43, 42, 41, 40])
    )

    # stop equals first item
    select_and_compare(
        RangeSelector(':40:-1', None, _format(40), -1),
        given_elements=elements,
        expected_selection=_format([56, 55, 47, 44, 43, 42, 41])
    )

    # stop is start's predecessor
    select_and_compare(
        RangeSelector('42:41:-1', _format(42), _format(41), -1),
        given_elements=elements,
        expected_selection=_format([42])
    )


def test_create_range_with_step_size_of_zero():
    with pytest.raises(ValueError):
        RangeSelector('::0', None, None, 0)


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_create_range_with_invalid_borders(kind):
    _format = get_formatter(kind)

    # start is greater than stop
    with pytest.raises(ValueError):
        RangeSelector('55:42', _format(55), _format(42))

    # stop is greater than start
    with pytest.raises(ValueError):
        RangeSelector('42:55:-1', _format(42), _format(55), -1)


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_range_select_when_stop_equals_start(kind):
    _format = get_formatter(kind)

    with pytest.raises(EmptySelectionError):
        RangeSelector('42:42', _format(42), _format(42)).select(_format(ELEMENTS))


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_range_select_when_stop_equals_first_element(kind):
    _format = get_formatter(kind)

    with pytest.raises(EmptySelectionError):
        RangeSelector(':40', None, _format(40)).select(_format(ELEMENTS))


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_range_select_when_stop_equals_last_element_and_with_negative_step_size(kind):
    _format = get_formatter(kind)

    with pytest.raises(EmptySelectionError):
        RangeSelector(':56:-1', None, _format(56), -1).select(_format(ELEMENTS))


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_range_select_with_missing_items(kind):
    _format = get_formatter(kind)
    elements = _format(ELEMENTS)

    # item specified as start is missing in items
    with pytest.raises(MissingElementError) as exception_info:
        RangeSelector('39:', _format(39), None).select(elements)

    error = exception_info.value
    assert error.element == _format(39)
    assert error.elements == elements

    # item specified as stop is missing in items
    with pytest.raises(MissingElementError) as exception_info:
        RangeSelector(':57', None, _format(57)).select(elements)

    error = exception_info.value
    assert error.element == _format(57)
    assert error.elements == elements


@pytest.mark.parametrize('kind', ['sequence', 'frame'])
def test_select_with_no_elements(kind):
    _format = get_formatter(kind)

    selectors = [
        SingleElementSelector('42', _format(42)),
        ListSelector('[42]', _format([42])),
        StarSelector(),
        DataSelector(),
        DataSynSelector(),
        RangeSelector(':', None, None)
    ]

    for selector in selectors:
        with pytest.raises(ValueError):
            selector.select([])