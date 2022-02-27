from numbers import Number
from typing import *

import nuke
from . import *

class WH_Knob(Array_Knob):
    """
    A knob which holds width and height values.
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

    def names(self,*args, **kwargs):
        """
        Return name for dimension 'i'.
        """
        return None

    def x(self,*args, **kwargs):
        """
        Return value for X position.
        """
        return None

    def y(self,*args, **kwargs):
        """
        Return value for Y position.
        """
        return None

    def x_at(self,*args, **kwargs):
        """
        Return value for X position at time 't'.
        """
        return None

    def y_at(self,*args, **kwargs):
        """
        Return value for Y position at time 't'.
        """
        return None