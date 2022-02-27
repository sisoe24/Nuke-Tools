from numbers import Number
from typing import *

import nuke
from . import *

class FrameRange(object):
    """
    A frame range, with an upper and lower bound and an increment.
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

    def first(self,):
        """
        self.first() -> int

        return the first frame of the range.
        """
        return int()

    def last(self,):
        """
        self.last() -> int

        return the last frame of the range.
        """
        return int()

    def increment(self,):
        """
        self.increment() -> int

        return the increment between two frames.
        """
        return int()

    def setFirst(self,n):
        """
        self.setFirst(n) -> None

        set the first frame of the range.
        """
        return None

    def setLast(self,n):
        """
        self.setLast(n) -> None

        set the last frame of the range.
        """
        return None

    def setIncrement(self,n):
        """
        self.setIncrement(n) -> None

        set the increment between two frames.
        """
        return None

    def frames(self,):
        """
        self.frames() -> int

        return the numbers of frames defined in the range.
        """
        return int()

    def getFrame(self,n):
        """
        self.getFrame(n) -> int

        return the frame according to the index, parameter n must be between 0 and frames().
        """
        return int()

    def isInRange(self,n):
        """
        self.isInRange(n) -> int

        return if the frame is inside the range.
        """
        return int()

    def minFrame(self,):
        """
        self.minFrame() -> int

        return the minimun frame define in the range.
        """
        return int()

    def maxFrame(self,):
        """
        self.maxFrame() -> int

        return the maximun frame define in the range.
        """
        return int()

    def stepFrame(self,):
        """
        self.stepFrame() -> int

        return the absolute increment between two frames.
        """
        return int()