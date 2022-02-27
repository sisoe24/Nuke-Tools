from numbers import Number
from typing import *

import nuke
from . import *

class Info(object):
    """
    An info object stores x, y, w and h values.
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

    def x(self,):
        """
        x() -> float

        Return left edge.
        """
        return float()

    def y(self,):
        """
        self.y() -> float

        Return the bottom edge.
        """
        return float()

    def w(self,):
        """
        self.w() -> float

        Return width.
        """
        return float()

    def h(self,):
        """
        self.h() -> float

        Return height.
        """
        return float()