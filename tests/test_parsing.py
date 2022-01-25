import itertools
from typing import Iterable, List, Tuple

import pytest

from ycbvideo.parsing import Parser, SelectionExpressionError

# parts valid for both sequence selection and frame selection
VALID_SELECTION_PARTS = [
    ('42', True),
    ('0042', True),
    ('0420', True),
    ('[42]', True),
    ('[0042,43,0440]', True),
    ('*', True)
]

# range selection parts, valid for both sequence selection and frame selection
VALID_RANGE_SELECTION_PARTS = [
    ('42:56', True),
    ('42:56:2', True),
    ('42:', True),
    ('42::2', True),
    (':56', True),
    (':56:2', True),
    (':', True),
    ('::', True),
    ('::-2', True),
    ('0042:56:', True)
]

# parts invalid both for sequence selection and frame selection
INVALID_SELECTION_PARTS = [
    ('', False),
    ('[]', False),
    ('[*]', False),
    ('[data]', False),
    ('[data_syn]', False),
    ('42,', False),
    ('42,43,44,', False),
    ('-42:', False),
    (':-56', False),
    ('47:42', False),
    ('42:47:-1', False),
    ('[:]', False),
    ('[::]', False),
    ('[42:]', False),
    ('[:56]', False),
    ('0000042', False)
]

# selections only valid for sequences
SPECIAL_SEQUENCE_SELECTIONS = [
    ('data_syn', True),
    ('data', True),
]

# selections only valid for frames
SPECIAL_FRAME_SELECTIONS = [
    # 6 digits only for frames
    ('000042', True),
    ('000420', True),
    ('000042:000047', True)
]

SEQUENCE_SELECTIONS = [
    *VALID_SELECTION_PARTS,
    *VALID_RANGE_SELECTION_PARTS,
    *INVALID_SELECTION_PARTS,
    *SPECIAL_SEQUENCE_SELECTIONS]
FRAME_SELECTIONS = [
    *VALID_SELECTION_PARTS,
    *VALID_RANGE_SELECTION_PARTS,
    *INVALID_SELECTION_PARTS,
    *SPECIAL_FRAME_SELECTIONS]


def combine_sequence_and_frame_selection(
        sequence_selection: Tuple[str, bool],
        frame_selection: Tuple[str, bool]) -> Tuple[str, bool]:
    sequence_expression, valid_sequence_expression = sequence_selection
    frame_expression, valid_frame_expression = frame_selection

    combined_expression = f"{sequence_expression}/{frame_expression}"
    if valid_sequence_expression and valid_frame_expression:
        return combined_expression, True

    return combined_expression, False


def combine_sequence_and_frame_selections(
        sequence_selections: List[Tuple[str, bool]],
        frame_selections: List[Tuple[str, bool]]) -> Iterable[Tuple[str, bool]]:

    for combination in itertools.product(sequence_selections, frame_selections):
        yield combine_sequence_and_frame_selection(combination[0], combination[1])


EXPRESSIONS_AND_VALIDITY = combine_sequence_and_frame_selections(SEQUENCE_SELECTIONS, FRAME_SELECTIONS)


@pytest.mark.parametrize('expression_and_validity', EXPRESSIONS_AND_VALIDITY)
def test_parse(expression_and_validity):
    expression, valid = expression_and_validity

    if valid:
        Parser.parse(expression)
    else:
        with pytest.raises(SelectionExpressionError):
            Parser.parse(expression)


def test_parse_exception():
    with pytest.raises(SelectionExpressionError) as exception_info:
        Parser.parse('invalid')

    error = exception_info.value
    assert error.expression == 'invalid'
