from pathlib import Path
import re
from typing import List, NamedTuple, Final, Union, Iterable

SELECTION_PATTERN: Final[str] = r'\[([0-9]{1,n}(,[0-9]{1,n})*)\]|([0-9]{1,n})|\*'
FRAMESEQUENCE_SELECTION_PATTERN: Final[str] = SELECTION_PATTERN.replace('n', '4') + r'|data_syn'
FRAME_SELECTION_PATTERN: Final[str] = SELECTION_PATTERN.replace('n', '6')
COMBINED_PATTERN: Final[re.Pattern] = re.compile(
    f"^(?P<framesequence>{FRAMESEQUENCE_SELECTION_PATTERN})/(?P<frame>{FRAME_SELECTION_PATTERN})$")
LIST_PATTERN: Final[re.Pattern] = re.compile(r'^\[(?P<items>[0-9]+(,[0-9]+)*)\]$')
SINGLE_ITEM_PATTERN: Final[re.Pattern] = re.compile(r'^(?P<item>[0-9]+|\*|data_syn)$')


class FrameSelector(NamedTuple):
    frame_sequence_selection: str
    frame_selection: str


def get_frame_selectors(selections: List[str]) -> List[FrameSelector]:
    frame_selectors = []

    for index, selection in enumerate(selections):
        try:
            frame_selectors.append(get_frame_selector(selection))
        except ValueError:
            raise ValueError(
                f"Selection syntax is incorrect: Selection '{selection}' at index {index}") from ValueError

    return frame_selectors


def is_star_selection(selection: List[str]) -> bool:
    return len(selection) == 1 and selection[0] == '*'


def get_frame_selector(selection: str) -> FrameSelector:
    if match := COMBINED_PATTERN.match(selection):
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


def format_selection_item(item: str, kind_of_item: str) -> str:
    if not (kind_of_item == 'frame_sequence' or kind_of_item == 'frame'):
        raise ValueError(
            f"Unknown kind of descriptor (has to be either 'frame_sequence' or 'frame'): {kind_of_item}")
    if item == '*' or item == 'data_syn':
        return item

    return "{:04d}".format(int(item)) if kind_of_item == 'frame_sequence' else "{:06d}".format(int(item))


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
