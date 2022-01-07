import abc
from abc import ABC
from pathlib import Path
import re
from typing import List, NamedTuple, Final, Union, Iterable, Optional, Literal, Tuple

NUMBERED_ITEM_MAX_DIGITS = 6
SPECIAL_FRAME_SEQUENCE_ITEMS: Final[List[str]] = ['data', 'data_syn']

# template still contain substring which have to be replaced before usage as a pattern like 'n'
NUMBERED_ITEM_TEMPLATE = r'[0-9]{1,n}'
# using fr, backslashes do not have to be escaped in f-strings
LIST_TEMPLATE = fr"\[{NUMBERED_ITEM_TEMPLATE}(,{NUMBERED_ITEM_TEMPLATE})*\]"
# 'item' can be replaced by 'sequence' or 'frame', which is necessary when the
# template is used twice in a pattern, since capture groups have to have unique names
RANGE_TEMPLATE = f"(?P<itemstart>{NUMBERED_ITEM_TEMPLATE})?:(?P<itemstop>{NUMBERED_ITEM_TEMPLATE})?" + \
                 f"(:(?P<itemstep>-?{NUMBERED_ITEM_TEMPLATE})?)?"
STAR_TEMPLATE = r'\*'

SINGLE_ITEM_PATTERN: Final[re.Pattern] = re.compile(r'^(?P<item>[0-9]+|\*|data|data_syn)$')
LIST_PATTERN: Final[re.Pattern] = re.compile(
    fr'^\[(?P<items>{NUMBERED_ITEM_TEMPLATE}(,{NUMBERED_ITEM_TEMPLATE})*)\]$'.replace(
        'n', str(NUMBERED_ITEM_MAX_DIGITS)))
RANGE_PATTERN: Final[re.Pattern] = re.compile(RANGE_TEMPLATE.replace('n', str(NUMBERED_ITEM_MAX_DIGITS)))


class RangeSelection(ABC):
    def __init__(self, start: Optional[str], stop: Optional[str], step: Optional[Union[int, str]]):
        self.start = self.check_start(start) if start else None
        self.stop = self.check_stop(stop) if stop else None
        self.step = RangeSelection.check_step(step) if step else None

    @abc.abstractmethod
    def check_start(self, start: Optional[str]) -> str:
        pass

    @abc.abstractmethod
    def check_stop(self, stop: Optional[str]) -> str:
        pass

    def as_tuple(self) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        return self.start, self.stop, self.step

    @staticmethod
    def check_step(step: Optional[Union[int, str]]) -> Optional[int]:
        if not isinstance(step, (int, str)):
            raise TypeError("step has to be of type 'int' or 'str'")

        if isinstance(step, str):
            # consider a possible minus sign
            if not step.lstrip('-').isdigit():
                raise ValueError(f"step represents no digit: {step}")
            step = int(step)

        if step == 0:
            raise ValueError('step must not be 0')

        return step


class SequenceRangeSelection(RangeSelection):
    def __init__(self, start: Optional[str], stop: Optional[str], step: Optional[Union[int, str]]):
        super().__init__(start, stop, step)

    def check_start(self, start):
        return normalize_numbered_sequence_selection_item(start)

    def check_stop(self, stop):
        return normalize_numbered_sequence_selection_item(stop)


class FrameRangeSelection(RangeSelection):
    def __init__(self, start: Optional[str], stop: Optional[str], step: Optional[Union[int, str]]):
        super().__init__(start, stop, step)

    def check_start(self, start):
        return normalize_numbered_frame_selection_item(start)

    def check_stop(self, stop):
        return normalize_numbered_frame_selection_item(stop)


def get_selection_expression_pattern() -> re.Pattern:
    # # most general pattern, valid for a frame sequence selection or a frame selection
    selection_template = f"{NUMBERED_ITEM_TEMPLATE}|{LIST_TEMPLATE}|{RANGE_TEMPLATE}|{STAR_TEMPLATE}"

    frame_selection_pattern = selection_template.replace('n', '6').replace('item', 'frame')

    frame_sequence_selection_pattern = selection_template.replace('n', '4').replace('item', 'sequence')
    for item in SPECIAL_FRAME_SEQUENCE_ITEMS:
        frame_sequence_selection_pattern += f"|{item}"

    return re.compile(
        f"^(?P<framesequence>{frame_sequence_selection_pattern})/(?P<frame>{frame_selection_pattern})$"
    )


SELECTION_EXPRESSION_PATTERN: Final[re.Pattern] = get_selection_expression_pattern()


class FrameSelector(NamedTuple):
    frame_sequence_selection: str
    frame_selection: str


def get_frame_selectors(selections: List[str]) -> List[FrameSelector]:
    frame_selectors = []

    for index, selection in enumerate(selections):
        try:
            frame_selectors.append(get_frame_selector(selection))
        except ValueError as error:
            raise ValueError(
                f"Selection syntax is incorrect: Selection '{selection}' at index {index}") from error

    return frame_selectors


def is_star_selection(selection: List[str]) -> bool:
    return len(selection) == 1 and selection[0] == '*'


def get_frame_selector(selection: str) -> FrameSelector:
    if match := SELECTION_EXPRESSION_PATTERN.match(selection):
        frame_sequence_selection = match.group('framesequence')
        frame_selection = match.group('frame')
# TODO validate range expression
        return FrameSelector(frame_sequence_selection, frame_selection)
    else:
        raise ValueError(f"Selection syntax is incorrect: '{selection}'")


def get_items(selection: str) -> List[str]:
    items = []
    if match := LIST_PATTERN.match(selection):
        items = [item for item in match.group('items').split(',')]
    elif match := SINGLE_ITEM_PATTERN.match(selection):
        items.append(match.group('item'))
    else:
        raise ValueError(f"Descriptor syntax is incorrect: {selection}")

    return items


def range_selection(selection: str, kind: Literal['sequence', 'frame']) -> Optional[RangeSelection]:
    if match := RANGE_PATTERN.match(selection):
        start = match.group('itemstart')
        stop = match.group('itemstop')
        step = match.group('itemstep')

        if kind == 'sequence':
            return SequenceRangeSelection(start, stop, step)
        elif kind == 'frame':
            return FrameRangeSelection(start, stop, step)

    return None


def normalize_sequence_selection_item(item: str) -> str:
    if not isinstance(item, str):
        raise TypeError('item must be a string')

    if item in ['*', *SPECIAL_FRAME_SEQUENCE_ITEMS]:
        return item

    try:
        return normalize_numbered_sequence_selection_item(item)
    except ValueError:
        raise ValueError(f"Invalid frame sequence selection item: {item}")


def normalize_numbered_sequence_selection_item(item: str) -> str:
    if item.isdigit() and len(item) <= 4:
        return "{:04d}".format(int(item))

    raise ValueError(
        f"Not a numbered frame sequence selection item: {item} (Must represent a digit and of length <= 4)")


def normalize_frame_selection_item(item: str) -> str:
    if not isinstance(item, str):
        raise TypeError('item must be a string')

    if item == '*':
        return item

    try:
        return normalize_numbered_frame_selection_item(item)
    except ValueError:
        raise ValueError(f"Invalid frame selection item: {item}")


def normalize_numbered_frame_selection_item(item: str) -> str:
    if item.isdigit() and len(item) <= 6:
        return "{:06d}".format(int(item))

    raise ValueError(
        f"Not a numbered frame selection item: {item} (Must represent a digit and of length <= 6)")


def load_frame_selectors_from_file(file: Union[Path, str]) -> Iterable[FrameSelector]:
    file_path = Path(file)

    if not file_path.exists():
        raise IOError(f"File does not exist: {file_path}")

    selectors = []
    with open(file_path, 'r') as f:
        for line_number, line in enumerate(f):
            # skip empty lines
            if line.rstrip():
                try:
                    selectors.append(get_frame_selector(line))
                except ValueError as error:
                    raise ValueError(f"Invalid selection syntax at line {line_number} in {file_path}") from error

    return selectors
