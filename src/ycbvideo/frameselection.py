from pathlib import Path
import re
from typing import List, NamedTuple, Final, Union, Iterable

SPECIAL_FRAME_SEQUENCE_ITEMS: Final[List[str]] = ['data', 'data_syn']
LIST_PATTERN: Final[re.Pattern] = re.compile(r'^\[(?P<items>[0-9]+(,[0-9]+)*)\]$')
SINGLE_ITEM_PATTERN: Final[re.Pattern] = re.compile(r'^(?P<item>[0-9]+|\*|data|data_syn)$')


def get_selection_expression_pattern() -> re.Pattern:
    numbered_item_pattern = r'([0-9]{1,n})'
    list_pattern = r'\[([0-9]{1,n}(,[0-9]{1,n})*)\]'
    star_pattern = r'\*'
    # most general pattern, valid for a frame sequence selection or a frame selection
    selection_pattern = f"{numbered_item_pattern}|{list_pattern}|{star_pattern}"

    frame_selection_pattern = selection_pattern.replace('n', '6')

    frame_sequence_selection_pattern =selection_pattern.replace('n', '4')
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


def normalize_sequence_selection_item(item: str) -> str:
    if item in ['*', *SPECIAL_FRAME_SEQUENCE_ITEMS]:
        return item
    elif item.isdigit() and len(item) <= 4:
        return "{:04d}".format(int(item))
    else:
        raise ValueError(f"Invalid frame sequence selection item: {item}")


def normalize_frame_selection_item(item: str) -> str:
    if item == '*':
        return item
    elif item.isdigit() and len(item) <= 6:
        return "{:06d}".format(int(item))
    else:
        raise ValueError(f"Invalid frame selection item: {item}")


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
