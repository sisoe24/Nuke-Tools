from numbers import Number
from typing import *

import nuke
from . import *

class BBox_Knob(Array_Knob):
    """
    A knob which holds a bounding box.
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
        Return name for dimension 'i'
        """
        return None

    def value(self,*args, **kwargs):
        """
        Return value for dimension 'i'
        """
        return None

    def x(self,*args, **kwargs):
        """
        Return value for X position.
        """
        return None

    def setX(self,*args, **kwargs):
        """
        Set value for X position.
        """
        return None

    def y(self,*args, **kwargs):
        """
        Return value for Y position.
        """
        return None

    def setY(self,*args, **kwargs):
        """
        Set value for Y position.
        """
        return None

    def r(self,*args, **kwargs):
        """
        Return value for R extent.
        """
        return None

    def setR(self,*args, **kwargs):
        """
        Set value for R extent.
        """
        return None

    def t(self,*args, **kwargs):
        """
        Return value for T extent.
        """
        return None

    def setT(self,*args, **kwargs):
        """
        Set value for T extent.
        """
        return None

    def toDict(self,):
        """
        self.toDict() -> dict.

        Returns the bounding box as a dict with x, y, r, and t keys.
        @return: dict with x, y, r and t keys
        """
        return dict()

    def fromDict(self, box:dict):
        """
        self.fromDict(box) -> None

        Set the bounding box from the given box.
        @param box: Dictionary containing the x, y, r and t keys.
        @return: None
        """
        return None