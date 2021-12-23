from pathlib import Path
from typing import Union


def validate_directory_path(path: Union[Path, str]) -> Path:
    path = Path(path)
    if not path.exists():
        raise IOError(f"Path does not exist: {path}")
    if not path.is_dir():
        raise IOError(f"Path is not a directory: {path}")

    return path
