from numbers import Number
from typing import *

import nuke
from . import *

class Keyer_Knob(Array_Knob):
    """
    Keyer_Knob
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

    def names(self, n:int):
        """
        self.names(n) -> string

        @param n: The index of the name to return.
        @return: The name at position n.
        """
        return str()

    def value(self, outputCtx, n:int):
        """
        self.value(outputCtx, n) -> float

        Get the value of argument n.
        @param outputCtx: The OutputContext to evaluate the argument in.
        @param n: The index of the argument to get the value of.
        @return: The value of argument n.
        """
        return float()

    def lowSoft(self,*args, **kwargs):
        """

        """
        return None

    def lowTol(self,*args, **kwargs):
        """

        """
        return None

    def highTol(self,*args, **kwargs):
        """

        """
        return None

    def highSoft(self,*args, **kwargs):
        """

        """
        return None