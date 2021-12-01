import pkgutil

from .loader import YcbVideoLoader

__version__ = pkgutil.get_data(__package__, 'VERSION').decode('utf-8')

__all__ = [
    'YcbVideoLoader'
]
