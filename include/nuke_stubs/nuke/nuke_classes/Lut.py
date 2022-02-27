from numbers import Number
from typing import *

import nuke
from . import *

class Lut(object):
    """
    Lut
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

    def isLinear(self,):
        """
        self.isLinear() -> True if toByte(x) appears to return x*255, False otherwise.
        """
        return bool()

    def isZero(self,):
        """
        self.isZero() -> True if toByte(0) returns a value <= 0, False otherwise.
        """
        return int()

    def toByte(self,float):
        """
        self.toByte(float) -> float.

        Converts floating point values to byte values in the range 0-255.
        """
        return float()

    def fromByte(self,float):
        """
        self.fromByte(float) -> float.

        Converts byte values in the range 0-255 to floating point.
        """
        return float()

    def toByte(self,float):
        """
        self.toByte(float) -> float.

        Converts floating point values to byte values in the range 0-255.
        """
        return float()

    def fromByte(self,float):
        """
        self.fromByte(float) -> float.

        Converts byte values in the range 0-255 to floating point.
        """
        return float()

    def toFloat(self,src, alpha):
        """
        toFloat(src, alpha) -> float list.

        Convert a sequence of floating-point values to to_byte(x)/255.
        Alpha is an optional argument and if present unpremultiply by alpha, convert, and then multiply back.
        """
        return list()

    def fromFloat(self,src, alpha):
        """
        fromFloat(src, alpha) -> float list.

        Convert a sequence of floating-point values to from_byte(x*255).
        Alpha is an optional argument and if present unpremultiply by alpha, convert, and then multiply back.
        """
        return list()

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None