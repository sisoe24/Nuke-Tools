from numbers import Number
from typing import *

import nuke
from . import *

class Int_Knob(Array_Knob):
    """
    A knob which holds one or more integer values.
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def __lt__(self, value, ):
        """
        Return self<value.
        """
        return None

    def __le__(self, value, ):
        """
        Return self<=value.
        """
        return None

    def __eq__(self, value, ):
        """
        Return self==value.
        """
        return None

    def __ne__(self, value, ):
        """
        Return self!=value.
        """
        return None

    def __gt__(self, value, ):
        """
        Return self>value.
        """
        return None

    def __ge__(self, value, ):
        """
        Return self>=value.
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
        Get the integer value of this knob.
        @return: The value of this knob as an int.
        """
        return int()

    def setValue(self, val:int):
        """
        self.setValue(val) -> bool
        Set the integer value of this knob.
        @param val: The new value. Must be an integer.
        @return: True if succeeded, False otherwise.
        """
        return bool()