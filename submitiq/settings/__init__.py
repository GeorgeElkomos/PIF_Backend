"""
Settings package initialization.
"""
from .base import *

# Import environment-specific settings
try:
    from .local import *
except ImportError:
    pass

try:
    from .production import *
except ImportError:
    pass
