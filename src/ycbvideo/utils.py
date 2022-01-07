from pathlib import Path
from typing import Union, Tuple, Optional, List, Literal


class RangeError(Exception):
    """Base class for exceptions raised in range expansion"""
    pass


class MissingItemError(RangeError):
    """Exception raised when an explicitly named item used as 'start' or 'stop' is missing"""
    def __init__(self, item: str, usage: Literal['start', 'stop'], message: str):
        self.item = item
        self.usage = usage
        self.message = message


def validate_directory_path(path: Union[Path, str]) -> Path:
    path = Path(path)
    if not path.exists():
        raise IOError(f"Path does not exist: {path}")
    if not path.is_dir():
        raise IOError(f"Path is not a directory: {path}")

    return path


def expand_range(item_range: Tuple[Optional[str], Optional[str], Optional[int]], items: List[str]) -> List[str]:
    if not items:
        raise RangeError("No items were given")
    if item_range[2] == 0:
        raise RangeError('Invalid range: Step size must not be 0')

    # step defaults to 1
    # step could be an int != 0 or None at this point
    step = item_range[2] or 1

    start = item_range[0]
    stop = item_range[1]

    if start:
        try:
            start_index = items.index(start)
        except ValueError as error:
            raise MissingItemError(start, 'start', f"Invalid range: Start '{start}' not in {items}") from error
    else:
        start_index = None

    if stop:
        try:
            stop_index = items.index(stop)
        except ValueError as error:
            raise MissingItemError(stop, 'stop', f"Invalid range: Stop '{stop}' not in {items}") from error
    else:
        stop_index = None

    expansion = items[slice(start_index, stop_index, step)]

    # an empty expansion is of no use and would be the result of
    # start > stop with a step size > 0 or
    # stop < start with a step size < 0 or
    # start == stop
    if not expansion:
        raise RangeError(f"Invalid range: Expansion is empty")

    return expansion
