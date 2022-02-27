from numbers import Number
from typing import *

import nuke
from . import *

class Box3_Knob(Array_Knob):
    """
    A 3-dimensional box.
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
        Return value for X position. X is the minimum horizontal extent of the box.
        """
        return None

    def setX(self,*args, **kwargs):
        """
        Set value for X position. X is the minimum horizontal extent of the box.
        """
        return None

    def y(self,*args, **kwargs):
        """
        Return value for Y position. Y is the minimum vertical extent of the box.
        """
        return None

    def setY(self,*args, **kwargs):
        """
        Set value for Y position. Y is the minimum vertical extent of the box.
        """
        return None

    def n(self,*args, **kwargs):
        """
        Return value for N position. N (near) is the minimum Z extent of the box.
        """
        return None

    def setN(self,*args, **kwargs):
        """
        Set value for N position. N (near) is the minimum Z extent of the box.
        """
        return None

    def r(self,*args, **kwargs):
        """
        Return value for R extent. R (right) is the right extent of the box.
        """
        return None

    def setR(self,*args, **kwargs):
        """
        Set value for R extent. R (right) is the right extent of the box.
        """
        return None

    def t(self,*args, **kwargs):
        """
        Return value for T extent. T (top) is the maximum vertical extent of the box.
        """
        return None

    def setT(self,*args, **kwargs):
        """
        Set value for T extent. T (top) is the maximum vertical extent of the box.
        """
        return None

    def f(self,*args, **kwargs):
        """
        Return value for F extent. F (far) is the maximum Z extent of the box.
        """
        return None

    def setF(self,*args, **kwargs):
        """
        Set value for F extent. F (far) is the maximum Z extent of the box.
        """
        return None