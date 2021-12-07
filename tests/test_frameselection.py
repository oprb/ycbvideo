import random
from typing import Iterable, List, Tuple, Union
import itertools

import pytest

from ycbvideo import frameselection
from ycbvideo.frameselection import FrameSelector

random.seed(42)

# parts valid for both sequence selection and frame selection
VALID_SELECTION_PARTS = [
    ('42', '42'),
    ('0042', '0042'),
    ('0420', '0420'),
    ('[42]', '[42]'),
    ('[0042,43,0440]', '[0042,43,0440]'),
    ('*', '*'),
]

# parts invalid both for sequence selection and frame selection
INVALID_SELECTION_PARTS = [
    ('', None),
    ('[]', None),
    ('[*]', None),
    ('42,', None),
    ('42,43,44,', None)
]

# selections only valid for sequences
SPECIAL_SEQUENCE_SELECTIONS = [
    ('data_syn', 'data_syn')
]

# selections only valid for frames
SPECIAL_FRAME_SELECTIONS = [
    # 6 digits only for frames
    ('000042', '000042'),
    ('000420', '000420')
]

SEQUENCE_SELECTIONS = [*VALID_SELECTION_PARTS, *INVALID_SELECTION_PARTS, *SPECIAL_SEQUENCE_SELECTIONS]
FRAME_SELECTIONS = [*VALID_SELECTION_PARTS, *INVALID_SELECTION_PARTS, *SPECIAL_FRAME_SELECTIONS]


def selection_expressions() -> Iterable[Tuple[str, Union[FrameSelector, None]]]:
    for selection in itertools.product(SEQUENCE_SELECTIONS, FRAME_SELECTIONS):
        sequence_selection, expected_sequence_selection = selection[0]
        frame_selection, expected_frame_selection = selection[1]

        if expected_sequence_selection is None or expected_frame_selection is None:
            yield f"{sequence_selection}/{frame_selection}", None
        else:
            yield f"{sequence_selection}/{frame_selection}",\
                  FrameSelector(expected_sequence_selection, expected_frame_selection)


def list_of_selection_expressions(amount: int) -> Iterable[Tuple[List[str], Union[List[FrameSelector], None]]]:
    number_of_sequence_selections = len(SEQUENCE_SELECTIONS)
    number_of_frame_selections = len(FRAME_SELECTIONS)

    for n in range(amount):
        valid = True
        list_of_expressions = []
        list_of_selectors = []
        for i in random.sample(range(number_of_sequence_selections), random.randrange(number_of_sequence_selections)):
            sequence_selection, expected_sequence_selection = SEQUENCE_SELECTIONS[i]
            for j in random.sample(range(number_of_frame_selections), random.randrange(number_of_frame_selections)):
                frame_selection, expected_frame_selection = FRAME_SELECTIONS[j]
                selection = f"{sequence_selection}/{frame_selection}"
                selector = FrameSelector(expected_sequence_selection, expected_frame_selection)

                if expected_sequence_selection is None or expected_frame_selection is None:
                    valid = False

                list_of_expressions.append(selection)
                list_of_selectors.append(selector)

        yield list_of_expressions, list_of_selectors if valid else None


def selection_items() -> Iterable[Tuple[str, Union[List[str], None]]]:
    selections: List[Tuple[str, Union[str, None]]] = [*SEQUENCE_SELECTIONS, *FRAME_SELECTIONS]

    for selection in selections:
        expression, expectation = selection

        if isinstance(expectation, str):
            yield expression, expectation.lstrip('[').rstrip(']').split(sep=',')
        else:
            yield expression, None


@pytest.mark.parametrize('selection_and_expectation', [*SEQUENCE_SELECTIONS, *FRAME_SELECTIONS])
def test_is_star_selection(selection_and_expectation):
    selection, expectation = selection_and_expectation

    assert frameselection.is_star_selection(selection) if expectation == '*'\
        else not frameselection.is_star_selection(selection)


@pytest.mark.parametrize('selection_and_expectation', selection_expressions())
def test_get_frame_selector(selection_and_expectation):
    selection, expectation = selection_and_expectation

    if isinstance(expectation, FrameSelector):
        assert frameselection.get_frame_selector(selection) == expectation
    elif expectation is None:
        with pytest.raises(ValueError):
            frameselection.get_frame_selector(selection)
    else:
        raise TypeError(f"Wrong input to test method: {selection_and_expectation}")


@pytest.mark.parametrize('selections_and_expectation', list_of_selection_expressions(100))
def test_get_frame_selectors(selections_and_expectation):
    selections, expectation = selections_and_expectation

    if isinstance(expectation, list):
        assert frameselection.get_frame_selectors(selections) == expectation
    elif expectation is None:
        with pytest.raises(ValueError):
            frameselection.get_frame_selectors(selections)
    else:
        raise TypeError(f"Wrong input to test method: {selections_and_expectation}")


@pytest.mark.parametrize('selection_and_expectation', selection_items())
def test_get_items(selection_and_expectation):
    selection, expectation = selection_and_expectation

    if isinstance(expectation, list):
        assert frameselection.get_items(selection) == expectation
    elif expectation is None:
        with pytest.raises(ValueError):
            frameselection.get_items(selection)
    else:
        raise TypeError(f"Wrong input to test method: {selection_and_expectation}")
