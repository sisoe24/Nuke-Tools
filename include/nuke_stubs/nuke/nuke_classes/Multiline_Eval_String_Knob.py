from numbers import Number
from typing import *

import nuke
from . import *

class Multiline_Eval_String_Knob(EvalString_Knob):
    """
    A knob which evaluates it's string value as a TCL expression. It provides a multiline text area when it appears in a Node panel.
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