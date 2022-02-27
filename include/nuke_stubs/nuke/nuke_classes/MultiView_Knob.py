from numbers import Number
from typing import *

import nuke
from . import *

class MultiView_Knob(Knob):
    """
    MultiView_Knob
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

    def fromScript(self,s):
        """
        fromScript(s) -> True if succeeded, False otherwise.

        Initialise from script s.
        """
        return bool()

    def fromScript(self,s):
        """
        fromScript(s) -> True if succeeded, False otherwise.

        Initialise from script s.
        """
        return bool()

    def toScriptPrefix(self,*args, **kwargs):
        """

        """
        return None

    def toScriptPrefixUserKnob(self,*args, **kwargs):
        """

        """
        return None

    def notDefault(self,):
        """
        notDefault() -> True if set to its default value, False otherwise.
        """
        return bool()

    def toScript(self,quote, context=None):
        """
        toScript(quote, context=current) -> string.

        Return the value of the knob in script syntax.
        Pass True for quote to return results quoted in {}.
        Pass None for context to get results for all views and key times (as stored in a .nk file).
        """
        return str()

    def toScript(self,quote, context=None):
        """
        toScript(quote, context=current) -> string.

        Return the value of the knob in script syntax.
        Pass True for quote to return results quoted in {}.
        Pass None for context to get results for all views and key times (as stored in a .nk file).
        """
        return str()