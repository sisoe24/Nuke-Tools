from numbers import Number
from typing import *

import nuke
from . import *

class BeginTabGroup_Knob(Knob):
    """
    Begin a group of tabs. Subsequent knobs will all be part of the same tab group, until a matching EndTabGroup knob is found.
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def __new__(self,*args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None