from numbers import Number
from typing import *

import nuke
from . import *

class ProgressTask(object):
    """
    ProgressTask
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

    def setProgress(self,i):
        """
        self.setProgress(i) -> None.

        i is an integer representing the current progress
        """
        return None

    def setMessage(self,s):
        """
        self.setMessage(s) -> None.

        set the message for the progress task
        """
        return None

    def isCancelled(self,):
        """
        self.isCancelled() -> True if the user has requested the task to be cancelled.
        """
        return bool()

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None