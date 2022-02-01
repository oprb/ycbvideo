import re
from typing import List, Literal, Optional, Tuple

from . import selectors, utils


def parse_selection_expressions(expressions: List[str]) -> List[selectors.Selector]:
    selectors = []
    for index, expression in enumerate(expressions):
        try:
            selector = Parser.parse(expression)
        except SelectionExpressionError as error:
            raise ValueError(f"Invalid selection expression: {expression} at index {0} in {expressions}") from error
        selectors.append(selector)

    return selectors


class Parser:
    _ELEMENT_TEMPLATE = r'[0-9]{1,6}'
    # using fr, backslashes do not have to be escaped in f-strings
    _LIST_TEMPLATE = fr"^\[(?P<elements>{_ELEMENT_TEMPLATE}(,{_ELEMENT_TEMPLATE})*)\]$"
    _RANGE_TEMPLATE = f"^(?P<start>{_ELEMENT_TEMPLATE})?:(?P<stop>{_ELEMENT_TEMPLATE})?" + \
                      f"(:(?P<step>-?{_ELEMENT_TEMPLATE})?)?$"

    _LIST_PATTERN = re.compile(_LIST_TEMPLATE)
    _RANGE_PATTERN = re.compile(_RANGE_TEMPLATE)

    @staticmethod
    def _single_element_expression(
            expression: str,
            kind: Literal['sequence', 'frame']) -> Optional[selectors.SingleElementSelector]:
        max_length = 4 if kind == 'sequence' else 6

        if expression.isdigit() and len(expression) <= max_length:
            normalized_element = utils.normalize_element(expression, kind)

            return selectors.SingleElementSelector(kind, expression, normalized_element)

        return None

    @staticmethod
    def _list_expression(expression: str, kind: Literal['sequence', 'frame']) -> Optional[selectors.ListSelector]:
        if match := Parser._LIST_PATTERN.match(expression):
            elements = match.group('elements').split(',')

            normalized_elements = [utils.normalize_element(element, kind) for element in elements]

            return selectors.ListSelector(kind, expression, normalized_elements)

        return None

    @staticmethod
    def _star_expression(expression: str, kind: Literal['sequence', 'frame']) -> Optional[selectors.StarSelector]:
        # star expression work the same for sequences and frames, therefore _kind is ignored
        # _kind is only specified to conform with the common signature
        return selectors.StarSelector(kind) if expression == '*' else None

    @staticmethod
    def _data_expression(expression: str, kind: str) -> Optional[selectors.DataSelector]:
        if kind != 'sequence':
            raise ValueError(f"kind must be 'sequence': {kind}")

        return selectors.DataSelector() if expression == 'data' else None

    @staticmethod
    def _data_syn_expression(expression: str, kind: str) -> Optional[selectors.DataSynSelector]:
        if kind != 'sequence':
            raise ValueError(f"kind must be 'sequence': {kind}")

        return selectors.DataSynSelector() if expression == 'data_syn' else None

    @staticmethod
    def _range_expression(expression: str, kind: Literal['sequence', 'frame']) -> Optional[selectors.RangeSelector]:
        if match := Parser._RANGE_PATTERN.match(expression):
            start = utils.normalize_optional_element(match.group('start'), kind)
            stop = utils.normalize_optional_element(match.group('stop'), kind)
            step = int(match.group('step') or 1)

            return selectors.RangeSelector(kind, expression, start, stop, step)

    @staticmethod
    def _get_sequence_and_frame_expression(expression: str) -> Tuple[str, str]:
        if expression.count('/') == 0:
            raise SelectionExpressionError(f"Expression contains no '/': {expression}", expression)
        if expression.count('/') > 1:
            raise SelectionExpressionError(f"Expression must contain only one '/': {expression}", expression)

        sequence_expression, frame_expression = expression.split('/')

        if not sequence_expression:
            raise SelectionExpressionError(f"No Sequence Expression given: {expression}", expression)
        if not frame_expression:
            raise SelectionExpressionError(f"No Frame Expression given: {expression}", expression)

        return sequence_expression, frame_expression

    @staticmethod
    def _parse_sequence_expression(expression: str):
        for expression_handler in [Parser._single_element_expression,
                                   Parser._list_expression,
                                   Parser._star_expression,
                                   Parser._data_expression,
                                   Parser._data_syn_expression,
                                   Parser._range_expression]:
            if selector := expression_handler(expression, 'sequence'):
                return selector

        # no expression handler matched
        raise SelectionExpressionError(f"Invalid sequence selection expression: {expression}", expression)

    @staticmethod
    def _parse_frame_expression(expression: str):
        for expression_handler in [Parser._single_element_expression,
                                   Parser._list_expression,
                                   Parser._star_expression,
                                   Parser._range_expression]:
            if selector := expression_handler(expression, 'frame'):
                return selector

        # no expression handler matched
        raise SelectionExpressionError(f"Invalid frame selection expression: {expression}", expression)

    @staticmethod
    def parse(expression: str):
        sequence_expression, frame_expression = Parser._get_sequence_and_frame_expression(expression)

        try:
            sequence_selector = Parser._parse_sequence_expression(sequence_expression)
            frame_selector = Parser._parse_frame_expression(frame_expression)
        except Exception as error:
            raise SelectionExpressionError(
                f"Selection expression could not be parsed: {expression}",
                expression) from error

        return selectors.Selector(expression, sequence_selector, frame_selector)


class SelectionExpressionError(Exception):
    def __init__(self, message: str, expression: str):
        super().__init__(message)
        self.expression = expression
