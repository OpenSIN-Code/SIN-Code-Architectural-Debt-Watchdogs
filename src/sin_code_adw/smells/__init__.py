"""Code smell detectors package.

Docs: __init__.py.doc.md
"""

from .god_function import detect as god_function
from .long_file import detect as long_file
from .circular_import import detect as circular_import
from .dead_code import detect as dead_code
from .deep_nesting import detect as deep_nesting

__all__ = ["god_function", "long_file", "circular_import", "dead_code", "deep_nesting"]
