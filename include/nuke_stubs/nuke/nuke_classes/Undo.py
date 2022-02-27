from numbers import Number
from typing import *

import nuke
from . import *

class Undo(object):
    """
    Undo
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

    def begin(self,*args, **kwargs):
        """
        Begin a new user-visible group of undo actions.
        """
        return None

    def name(self,*args, **kwargs):
        """
        Name current undo set.
        """
        return None

    def end(self,*args, **kwargs):
        """
        Complete current undo set and add it to the undo list.
        """
        return None

    def new(self,*args, **kwargs):
        """
        Same as end();begin().
        """
        return None

    def cancel(self,*args, **kwargs):
        """
        Undoes any actions recorded in the current set and throws it away.
        """
        return None

    def undoSize(self,*args, **kwargs):
        """
        Number of undo's that can be done.
        """
        return None

    def redoSize(self,*args, **kwargs):
        """
        Number of redo's that can be done.
        """
        return None

    def undoTruncate(self,*args, **kwargs):
        """
        Destroy any undo's greater or equal to n.
        """
        return None

    def redoTruncate(self,*args, **kwargs):
        """
        Destroy any redo's greater or equal to n.
        """
        return None

    def undoDescribe(self,*args, **kwargs):
        """
        Return short description of undo n.
        """
        return None

    def redoDescribe(self,*args, **kwargs):
        """
        Return short description of redo n.
        """
        return None

    def undoDescribeFully(self,*args, **kwargs):
        """
        Return long description of undo n.
        """
        return None

    def redoDescribeFully(self,*args, **kwargs):
        """
        Return long description of redo n.
        """
        return None

    def undo(self,*args, **kwargs):
        """
        Undoes 0'th undo.
        """
        return None

    def redo(self,*args, **kwargs):
        """
        Redoes 0'th redo.
        """
        return None

    def disable(self,*args, **kwargs):
        """
        Prevent recording undos until matching enable()
        """
        return None

    def enable(self,*args, **kwargs):
        """
        Undoes the previous disable()
        """
        return None

    def disabled(self,*args, **kwargs):
        """
        True if disable() has been called
        """
        return None

    def __enter__(self,*args, **kwargs):
        """

        """
        return None

    def __exit__(self,*args, **kwargs):
        """

        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None