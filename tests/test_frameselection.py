import itertools
import random
from typing import Iterable, List, Tuple, Union, Optional, Literal

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

VALID_SEQUENCE_SELECTIONS = [*VALID_SELECTION_PARTS, *SPECIAL_SEQUENCE_SELECTIONS]
VALID_FRAME_SELECTIONS = [*VALID_SELECTION_PARTS, *SPECIAL_FRAME_SELECTIONS]
SEQUENCE_SELECTIONS = [*VALID_SELECTION_PARTS, *INVALID_SELECTION_PARTS, *SPECIAL_SEQUENCE_SELECTIONS]
FRAME_SELECTIONS = [*VALID_SELECTION_PARTS, *INVALID_SELECTION_PARTS, *SPECIAL_FRAME_SELECTIONS]


def combine_sequence_and_frame_selection(
        sequence_selection: Tuple[str, Optional[str]],
        frame_selection: Tuple[str, Optional[str]],
        result_type: Literal['str', 'selector']) -> Tuple[str, Optional[Union[str, FrameSelector]]]:
    sequence_expression, expected_sequence_selection = sequence_selection
    frame_expression, expected_frame_selection = frame_selection

    combined_expression = f"{sequence_expression}/{frame_expression}"
    if expected_sequence_selection is None or expected_frame_selection is None:
        return combined_expression, None

    if result_type == 'str':
        return combined_expression, f"{expected_sequence_selection}/{expected_frame_selection}"
    if result_type == 'selector':
        return combined_expression, FrameSelector(expected_sequence_selection, expected_frame_selection)


def combine_sequence_and_frame_selections(
        sequence_selections: List[Tuple[str, Optional[str]]],
        frame_selections: List[Tuple[str, Optional[str]]],
        result_type: Literal['str', 'selector']) -> Iterable[Tuple[str, Optional[Union[str, FrameSelector]]]]:

    for selection in itertools.product(sequence_selections, frame_selections):
        yield combine_sequence_and_frame_selection(selection[0], selection[1], result_type)


def expression_and_selector() -> Iterable[Tuple[str, Optional[FrameSelector]]]:
    for selection in itertools.product(SEQUENCE_SELECTIONS, FRAME_SELECTIONS):
        yield combine_sequence_and_frame_selection(selection[0], selection[1], result_type='selector')


def list_of_expressions_and_list_of_selectors(
        amount: int) -> Iterable[Tuple[List[str], Optional[List[FrameSelector]]]]:
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


def expression_and_items() -> Iterable[Tuple[str, Optional[List[str]]]]:
    selections: List[Tuple[str, Optional[str]]] = [*SEQUENCE_SELECTIONS, *FRAME_SELECTIONS]

    for selection in selections:
        expression, expectation = selection

        if isinstance(expectation, str):
            yield expression, expectation.lstrip('[').rstrip(']').split(sep=',')
        else:
            yield expression, None


def get_random_subset(collection: Iterable,
                      minimum_number_of_elements: int = 0,
                      maximum_number_of_elements: Optional[int] = None) -> Iterable:
    elements = [*collection]
    bfs = min(maximum_number_of_elements, len(elements)) if maximum_number_of_elements else len(elements)
    number_of_elements = random.randint(
        minimum_number_of_elements,
        # make sure that the number of elements is not exceeded
        min(maximum_number_of_elements, len(elements)) if maximum_number_of_elements else len(elements))
    return random.sample(elements, number_of_elements)


@pytest.mark.parametrize('selection_and_expectation', [*SEQUENCE_SELECTIONS, *FRAME_SELECTIONS])
def test_is_star_selection(selection_and_expectation):
    selection, expectation = selection_and_expectation

    assert frameselection.is_star_selection(selection) if expectation == '*'\
        else not frameselection.is_star_selection(selection)


@pytest.mark.parametrize('expression_and_selector', expression_and_selector())
def test_get_frame_selector(expression_and_selector):
    selection, expectation = expression_and_selector

    if isinstance(expectation, FrameSelector):
        assert frameselection.get_frame_selector(selection) == expectation
    elif expectation is None:
        with pytest.raises(ValueError):
            frameselection.get_frame_selector(selection)
    else:
        raise TypeError(f"Wrong input to test method: {expression_and_selector}")


@pytest.mark.parametrize('list_of_expressions_and_list_of_selectors', list_of_expressions_and_list_of_selectors(100))
def test_get_frame_selectors(list_of_expressions_and_list_of_selectors):
    selections, expectation = list_of_expressions_and_list_of_selectors

    if isinstance(expectation, list):
        assert frameselection.get_frame_selectors(selections) == expectation
    elif expectation is None:
        with pytest.raises(ValueError):
            frameselection.get_frame_selectors(selections)
    else:
        raise TypeError(f"Wrong input to test method: {list_of_expressions_and_list_of_selectors}")


@pytest.mark.parametrize('expression_and_items', expression_and_items())
def test_get_items(expression_and_items):
    selection, expectation = expression_and_items

    if isinstance(expectation, list):
        assert frameselection.get_items(selection) == expectation
    elif expectation is None:
        with pytest.raises(ValueError):
            frameselection.get_items(selection)
    else:
        raise TypeError(f"Wrong input to test method: {expression_and_items}")


def test_load_frame_selectors_from_file(tmp_path):
    from ycbvideo.frameselection import load_frame_selectors_from_file
    non_existent_file = tmp_path / 'non_existent_file'
    file_with_valid_content = tmp_path / 'file_with_valid_content'
    file_with_new_line_at_the_end = tmp_path / 'file_with_new_line_at_the_end'
    file_with_invalid_content = tmp_path / 'file_with_invalid_content'
    empty_file = tmp_path / 'empty_file'

    # test with file with correct expressions only
    selections = combine_sequence_and_frame_selections(VALID_SEQUENCE_SELECTIONS,
                                                       VALID_FRAME_SELECTIONS,
                                                       result_type='selector')

    valid_expressions, expected_selections = map(list, zip(*get_random_subset(selections)))
    with open(file_with_valid_content, 'w') as f:
        for expression in valid_expressions:
            f.write(expression + '\n')

    assert load_frame_selectors_from_file(file_with_valid_content) == expected_selections,\
        "read file with valid expressions"

    # test with file with correct expressions and newline at the end of file
    with open(file_with_new_line_at_the_end, 'w') as f:
        for expression in valid_expressions:
            f.write(expression + '\n')

        f.write('\n')

    assert load_frame_selectors_from_file(file_with_new_line_at_the_end) == expected_selections,\
        "read file with new line at the end"

    # test with file containing not only valid expressions
    invalid_selections = get_random_subset(
        [*combine_sequence_and_frame_selections(VALID_SEQUENCE_SELECTIONS, INVALID_SELECTION_PARTS, result_type='str'),
         *combine_sequence_and_frame_selections(INVALID_SELECTION_PARTS, VALID_FRAME_SELECTIONS, result_type='str')],
        minimum_number_of_elements=1,
        maximum_number_of_elements=1)
    invalid_expressions, _ = map(list, zip(*invalid_selections))
    expressions = [*valid_expressions, *invalid_expressions]
    random.shuffle(expressions)
    with open(file_with_invalid_content, 'w') as f:
        for expression in expressions:
            f.write(expression + '\n')

    with pytest.raises(ValueError):
        load_frame_selectors_from_file(file_with_invalid_content)

    # test with non-existent file
    with pytest.raises(IOError):
        load_frame_selectors_from_file(non_existent_file)

    # test with path given as a str and empty file
    empty_file.touch()

    assert load_frame_selectors_from_file(str(empty_file)) == []
