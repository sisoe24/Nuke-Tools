from numbers import Number
from typing import *

import nuke
from . import *

class ColorChip_Knob(Unsigned_Knob):
    """
    A knob which holds a single unsigned int that describes a user interface colour. The color format is 0xRRGGBB00.
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None

    def __new__(self,*args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        return None