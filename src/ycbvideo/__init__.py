import pkgutil

from .loader import Loader
from .frame_access import Frame, FrameAccessObject, Descriptor, Box

__version__ = pkgutil.get_data(__package__, 'VERSION').decode('utf-8').rstrip()

__all__ = [
    'Loader',
    'FrameAccessObject',
    'Frame',
    'Descriptor',
    'Box'
]
