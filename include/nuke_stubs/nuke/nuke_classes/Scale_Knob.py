from numbers import Number
from typing import *

import nuke
from . import *

class Scale_Knob(Array_Knob):
    """
    Scale_Knob
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

    def names(self,n):
        """
        names(n) -> string

        Return name for dimension n. The argument n is an integer.
        """
        return str()

    def value(self,n, oc):
        """
        value(n, oc) -> float

        Return value for dimension n. The optional argument oc is an OutputContext.
        """
        return float()

    def x(self,oc):
        """
        x(oc) -> float

        Return value for x. The optional oc argument is an OutputContext
        """
        return float()

    def y(self,oc):
        """
        y(oc) -> float

        Return value for y. The optional oc argument is an OutputContext
        """
        return float()

    def z(self,oc):
        """
        z(oc) -> float

        Return value for z. The optional oc argument is an OutputContext
        """
        return float()