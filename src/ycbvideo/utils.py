from pathlib import Path
import re
from typing import Union, List


def get_frame_set_index(frame_set: Union[str, int]) -> str:
    if not isinstance(frame_set, str) or not isinstance(frame_set, int):
        raise TypeError("Index has to be of type 'str' or type 'int'")

    index = frame_set
    if isinstance(frame_set, str):
        if match := re.match(r'00(?P<index>[0-9]{2})', frame_set):
            index = int(match.group('index'))
        else:
            raise ValueError(f"Index has wrong format: {frame_set}")

    if not 0 <= frame_set <= 91:
        raise ValueError(f"Index has to be a value between 0 and 91: {frame_set}")

    return "{:04d}".format(frame_set)


def validate_directory_path(path: Union[Path, str]) -> Path:
    path = Path(path)
    if not path.exists():
        raise IOError(f"Path does not exist: {path}")
    if not path.is_dir():
        raise IOError(f"Path is not a directory: {path}")

    return path

