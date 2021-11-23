import re
from typing import List, NamedTuple
import datatypes


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
    selection_pattern = r'\[([0-9]{1,n}(,[0-9]{1,n})*)\]|([0-9]{1,n})|\*'
    frameset_selection_pattern = selection_pattern.replace('n', '4')
    frame_selection_pattern = selection_pattern.replace('n', '6')
    combined_pattern = re.compile(
        f"^(?P<frameset>{frame_selection_pattern}):(?P<frame>{frameset_selection_pattern})$")

    if match := combined_pattern.match(selection):
        frame_set_selection = match.group('frameset')
        frame_selection = match.group('frame')

        return FrameSelector(frame_set_selection, frame_selection)
    else:
        raise ValueError(f"Selection syntax is incorrect: '{selection}'")


def get_items(selection: str) -> List[str]:
    list_pattern = re.compile(r'^\[(?P<items>[0-9]+(,[0-9]+)*)\]$')
    single_item_pattern = re.compile(r'^(?P<item>[0-9]+|\*)$')

    items = []
    if match := list_pattern.match(selection):
        items = [item for item in match.group('items').split(',')]
    elif match := single_item_pattern.match(selection):
        items.append(match.group('item'))
    else:
        raise ValueError(f"Descriptor syntax is incorrect: {selection}")

    return items


def format_selection_item(item: str, kind_of_item: str) -> str:
    if not (kind_of_item == 'frame_sequence' or kind_of_item == 'frame'):
        raise ValueError(
            f"Unknown kind of descriptor (has to be either 'frame_sequence' or 'frame'): {kind_of_item}")
    if item == '*':
        return item

    return "{:04d}".format(int(item)) if kind_of_item == 'frame_sequence' else "{:06d}".format(int(item))
