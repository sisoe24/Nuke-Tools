from numbers import Number
from typing import *

import nuke
from . import *

class Unsigned_Knob(Array_Knob):
    """
    A knob which holds one or more unsigned integer values.
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

    def value(self,):
        """
        self.value() -> int
        Get the value of this knob as an integer.
        @return: int
        """
        return int()

    def setValue(self, val:int):
        """
        self.setValue(val) -> bool
        Set the unsigned integer value of this knob.
        @param val: The new value for the knob. Must be an integer >= 0.
        @return: True if succeeded, False otherwise.
        """
        return bool()