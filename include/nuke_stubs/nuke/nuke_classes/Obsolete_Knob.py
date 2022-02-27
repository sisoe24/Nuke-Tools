from numbers import Number
from typing import *

import nuke
from . import *

class Obsolete_Knob(Knob):
    """
    For internal use only.
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

    def value(self,*args, **kwargs):
        """
        Return value at the current frame for channel 'c'.
        """
        return None

    def setValue(self,val, chan):
        """
        self.setValue(val, chan) -> bool

        Sets the value 'val' at channel 'chan'.
        @return: True if successful, False if not.
        """
        return bool()