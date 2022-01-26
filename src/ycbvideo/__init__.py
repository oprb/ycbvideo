import pkgutil

from .loader import Loader
from .datatypes import Frame, Descriptor, Box

__version__ = pkgutil.get_data(__package__, 'VERSION').decode('utf-8').rstrip()

__all__ = [
    'Loader',
    'Frame',
    'Descriptor',
    'Box'
]
