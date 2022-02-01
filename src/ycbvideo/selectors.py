from abc import ABC, abstractmethod
from typing import List, Literal, Optional


class ElementSelector(ABC):
    @abstractmethod
    def select(self, elements: List[str]) -> List[str]:
        raise NotImplementedError

    @staticmethod
    def check_elements_to_select_from(elements: List[str]):
        if not elements:
            raise ValueError("No elements to select from")


class SingleElementSelector(ElementSelector):
    def __init__(self, kind: Literal['sequence', 'frame'], expression: str, element: str):
        self._kind = kind
        self._expression = expression
        self._element_to_select = element

    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        if self._element_to_select not in elements:
            raise MissingElementError(
                message=f"Single element missing: {self._kind} {self._expression}",
                element=self._element_to_select,
                elements=elements)

        return [self._element_to_select]


class ListSelector(ElementSelector):
    def __init__(self, kind: Literal['sequence', 'frame'], expression: str, elements: List[str]):
        self._kind = kind
        self._expression = expression
        self._elements_to_select = elements

    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        for index, element in enumerate(self._elements_to_select):
            if element not in elements:
                raise MissingElementError(
                    message='List element missing:' +
                            f" {self._kind } {self.get_list_expression_element(index)} at index {index}",
                    element=element,
                    elements=elements)

        return self._elements_to_select

    def get_list_expression_element(self, index: int) -> str:
        return self._expression.lstrip('[').rstrip(']').split(',')[index]


class StarSelector(ElementSelector):
    def __init__(self, kind: Literal['sequence', 'frame']):
        self._kind = kind

    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        return elements


class DataSelector(ElementSelector):
    def __init__(self):
        self._kind = 'sequence'

    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        return [element for element in elements if element != 'data_syn']


class DataSynSelector(ElementSelector):
    def __init__(self):
        self._kind = 'sequence'

    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        if 'data_syn' not in elements:
            raise MissingElementError(
                message="data_syn sequence missing",
                element='data_syn',
                elements=elements
            )

        return ['data_syn']


class RangeSelector(ElementSelector):
    def __init__(self,
                 kind: Literal['sequence', 'frame'],
                 expression: str, start: Optional[str],
                 stop: Optional[str],
                 step: int = 1):
        self._kind = kind
        self._expression = expression

        self.check_range_elements(start, stop, step)
        self._start = start
        self._stop = stop
        self._step = step

    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        if self._kind == 'sequence':
            # data_syn has to be excluded
            elements = [element for element in elements if element.isdigit()]

        if self._start:
            try:
                start_index = elements.index(self._start)
            except ValueError as error:
                raise MissingElementError(
                    f"Range start element missing: {self._expression}", self._start, elements) from error
        else:
            start_index = None

        if self._stop:
            try:
                stop_index = elements.index(self._stop)
            except ValueError as error:
                raise MissingElementError(
                    f"Range stop element missing: {self._kind} {self._stop}",
                    self._stop,
                    elements) from error
        else:
            stop_index = None

        expansion = elements[slice(start_index, stop_index, self._step)]

        # an empty expansion is of no use and would be the result of
        # start == stop
        # start = None, stop == first element and step size > 1
        # start = last element, stop == last element and step size < -1
        if not expansion:
            raise EmptySelectionError(f"No elements selected: {self._expression}", self._expression, elements)

        return expansion

    def check_range_elements(self, start: Optional[str], stop: Optional[str], step: int):
        """
        Check for correct values for start, stop and step.

        Cases, where "expanding" the range, i.e. selecting all elements which
        lay in the range borders, results in an empty selection are not
        handled here since not all of them could be detected at this point.
        'start == stop' (resulting in an empty expansion) is an example,
        which could be detected at this point, but cases like
        'start == None and stop equals the first available element'
        can only be detected while expanding.
        """
        if step == 0:
            raise ValueError(f"step must not be 0")

        if start and stop:
            if step > 0 and int(start) > int(stop):
                raise ValueError(f"step > 0 requires start < stop: {self._expression}")

            if step < 0 and int(start) < int(stop):
                raise ValueError(f"step < 0 requires start > stop: {self._expression}")


class Selector:
    def __init__(self, expression: str, sequence_selector: ElementSelector, frame_selector: ElementSelector):
        self._expression = expression
        self._sequence_selector = sequence_selector
        self._frame_selector = frame_selector

    def select_sequences(self, sequences: List[str]) -> List[str]:
        return self._sequence_selector.select(sequences)

    def select_frames(self, frames: List[str]) -> List[str]:
        return self._frame_selector.select(frames)


class SelectionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class MissingElementError(SelectionError):
    def __init__(self, message: str, element: str, elements: List[str]):
        super().__init__(message)
        self.element = element
        self.elements = elements


class EmptySelectionError(SelectionError):
    def __init__(self, message: str, expression: str, elements: List[str]):
        super().__init__(message)
        self.expression = expression
        self.elements = elements
