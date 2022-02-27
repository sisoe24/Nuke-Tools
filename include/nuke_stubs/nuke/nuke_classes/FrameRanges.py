from numbers import Number
from typing import *

import nuke
from . import *

class FrameRanges(object):
    """
    A sequence of FrameRange objects with convenience functions for iterating over all frames in all ranges.
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def __str__(self, ):
        """
        Return str(self).
        """
        return None

    def __iter__(self, ):
        """
        Implement iter(self).
        """
        return None

    def __next__(self, ):
        """
        Implement next(self).
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

    def size(self,):
        """
        size() -> int

        return the ranges number.
        """
        return int()

    def add(self,r):
        """
        add(r) -> None

        add a new frame range.
        """
        return None

    def minFrame(self,):
        """
        minFrame() -> int

        get minimun frame of all ranges.
        """
        return int()

    def maxFrame(self,):
        """
        maxFrame() -> int

        get maximun frame of all ranges.
        """
        return int()

    def clear(self,):
        """
        clear() -> None

        reset all store frame ranges.
        """
        return None

    def compact(self,):
        """
        compact() -> None

        compact all the frame ranges.
        """
        return None

    def toFrameList(self,):
        """
        toFrameList() -> [int]

        return a list of frames in a vector
        """
        return [int]

    def getRange(self,):
        """
        getRange()-> FrameRange

        return a range from the list
        """
        return FrameRange()