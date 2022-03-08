from pathlib import Path
from typing import Union, Optional, Literal


def validate_directory_path(path: Union[Path, str]) -> Path:
    path = Path(path)
    if not path.exists():
        raise IOError(f"Path does not exist: {path}")
    if not path.is_dir():
        raise IOError(f"Path is not a directory: {path}")

    return path


def check_kind(kind: str):
    if kind not in ['sequence', 'frame']:
        raise ValueError(f"kind has to be either 'sequence' or 'frame': {kind}")


def normalize_element(element: str, kind: Literal['sequence', 'frame']) -> str:
    check_kind(kind)

    if not element.isdigit():
        raise ValueError(f"element must be a digit: {element}")

    if kind == 'sequence' and len(element) > 4:
        raise ValueError(f"sequence element must be of length <= 4: {element}")
    elif kind == 'frame' and len(element) > 6:
        raise ValueError(f"frame element must be of length <= 6: {element}")

    if kind == 'sequence':
        return "{:04d}".format(int(element))
    else:
        return "{:06d}".format(int(element))


def normalize_optional_element(element: Optional[str], kind: Literal['sequence', 'frame']) -> Optional[str]:
    if element is None:
        return element

    return normalize_element(element, kind)
