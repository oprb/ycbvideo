from abc import ABC, abstractmethod
from typing import List, Optional


class ElementSelector(ABC):
    @abstractmethod
    def select(self, elements: List[str]) -> List[str]:
        raise NotImplementedError

    @staticmethod
    def check_elements_to_select_from(elements: List[str]):
        if not elements:
            raise ValueError("No elements to select from")


class SingleElementSelector(ElementSelector):
    def __init__(self, expression: str, element: str):
        self.expression = expression
        self.element_to_select = element

    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        if self.element_to_select not in elements:
            raise MissingElementError(
                message=f"Single element missing: {self.expression}",
                element=self.element_to_select,
                elements=elements)

        return [self.element_to_select]


class ListSelector(ElementSelector):
    def __init__(self, expression: str, elements: List[str]):
        self.expression = expression
        self.elements_to_select = elements

    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        for index, element in enumerate(self.elements_to_select):
            if element not in elements:
                raise MissingElementError(
                    message=f"List element missing: {self.get_list_expression_element(index)} at index {index}",
                    element=element,
                    elements=elements)

        return self.elements_to_select

    def get_list_expression_element(self, index: int) -> str:
        return self.expression.lstrip('[').rstrip(']').split(',')[index]


class StarSelector(ElementSelector):
    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        return elements


class DataSelector(ElementSelector):
    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        return [element for element in elements if element != 'data_syn']


class DataSynSelector(ElementSelector):
    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        if 'data_syn' not in elements:
            raise MissingElementError(
                message="'data_syn' sequence missing",
                element='data_syn',
                elements=elements
            )

        return ['data_syn']


class RangeSelector(ElementSelector):
    def __init__(self, expression: str, start: Optional[str], stop: Optional[str], step: int = 1):
        self.expression = expression

        self.check_range_elements(start, stop, step)
        self.start = start
        self.stop = stop
        self.step = step

    def select(self, elements: List[str]) -> List[str]:
        ElementSelector.check_elements_to_select_from(elements)

        if self.start:
            try:
                start_index = elements.index(self.start)
            except ValueError as error:
                raise MissingElementError(
                    f"Range start element missing: {self.expression}", self.start, elements) from error
        else:
            start_index = None

        if self.stop:
            try:
                stop_index = elements.index(self.stop)
            except ValueError as error:
                raise MissingElementError(f"Range stop element missing: {self.stop}", self.stop, elements) from error
        else:
            stop_index = None

        expansion = elements[slice(start_index, stop_index, self.step)]

        # an empty expansion is of no use and would be the result of
        # start == stop
        # start = None, stop == first element and step size > 1
        # start = last element, stop == last element and step size < -1
        if not expansion:
            raise EmptySelectionError(f"No elements selected: {self.expression}", self.expression, elements)

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
                raise ValueError(f"step > 0 requires start < stop: {self.expression}")

            if step < 0 and int(start) < int(stop):
                raise ValueError(f"step < 0 requires start > stop: {self.expression}")


class Selector:
    def __init__(self, expression: str, sequence_selector: ElementSelector, frame_selector: ElementSelector):
        self.expression = expression
        self.sequence_selector = sequence_selector
        self.frame_selector = frame_selector

    def select_sequences(self, sequences: List[str]) -> List[str]:
        return self.sequence_selector.select(sequences)

    def select_frames(self, frames: List[str]) -> List[str]:
        return self.frame_selector.select(frames)


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
