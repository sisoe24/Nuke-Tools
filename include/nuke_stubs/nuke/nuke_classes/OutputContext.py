from numbers import Number
from typing import *

import nuke
from . import *

class OutputContext(object):
    """
    Describes a context in which expressions can be evaluated.
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

    def view(self,):
        """
        view() -> int

        Return view number.
        """
        return int()

    def setView(self,n):
        """
        setView(n) -> True

        Set view number. The n argument is an integer in the range of 0 to number of views.
        """
        return True

    def frame(self,):
        """
        frame() -> float

        Return frame value.
        """
        return float()

    def setFrame(self,f):
        """
        setFrame(f) -> True

        Set frame value. The f argument is a float.
        """
        return True

    def viewname(self,n):
        """
        viewname(n) -> string

        Return name of the view. The n argument is an integer in the range of 0 to number of views.
        """
        return str()

    def viewshort(self,n):
        """
        viewshort(n) -> string

        Return short name of the view. The n argument is an integer in the range of 0 to number of views.
        """
        return str()

    def viewcount(self,):
        """
        viewcount() -> int

        Return number of views.
        """
        return int()

    def viewFromName(self,name):
        """
        viewFromName(name) -> int

        Returns the index of the view with name matching the argument name or -1 if there is no match.
        """
        return int()

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None