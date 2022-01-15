import pkgutil

from .loader import YcbVideoLoader
from .datatypes import Frame, FrameDescriptor, Box

__version__ = pkgutil.get_data(__package__, 'VERSION').decode('utf-8').rstrip()

__all__ = [
    'YcbVideoLoader',
    'Frame',
    'FrameDescriptor',
    'Box'
]
