from numbers import Number
from typing import *

import nuke
from . import *

class Transform2d_Knob(Knob):
    """
    Transform2d_Knob
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

    def value(self,oc):
        """
        value(oc) -> matrix

        Return transformation matrix. The argument oc is an OutputContext. Both arguments are optional.
        """
        return Any