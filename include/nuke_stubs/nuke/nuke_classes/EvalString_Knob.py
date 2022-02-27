from numbers import Number
from typing import *

import nuke
from . import *

class EvalString_Knob(String_Knob):
    """
    A string-valued knob which evaluates it's value as a TCL expression.
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

    def evaluate(self,):
        """
        self.evaluate() -> String.
        Evaluate the string, performing substitutions.
        @return: String.
        """
        return str()