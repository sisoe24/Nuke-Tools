from numbers import Number
from typing import *

import nuke
from . import *

class CancelledError(Exception):
    """
    Common base class for all non-exit exceptions.
    """
    @property
    def __weakref__(self) -> Any:
        """
        list of weak references to the object (if defined)
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None