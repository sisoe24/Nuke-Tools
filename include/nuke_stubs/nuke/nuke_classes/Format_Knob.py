from numbers import Number
from typing import *

import nuke
from . import *

class Format_Knob(Knob):
    """
    Format_Knob
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

    def name(self,):
        """
        name() -> string.

        Return name of knob.
        """
        return str()

    def value(self,):
        """
        value() -> Format.

        Return value of knob.
        """
        return Format()

    def actualValue(self,):
        """
        actualValue() -> Format.

        Return value of knob.
        """
        return Format()

    def setValue(self,format):
        """
        setValue(format) -> True if succeeded, False otherwise.

        Set value of knob to format (either a Format object or a name of a format, e.g. "NTSC").
        """
        return bool()

    def fromScript(self,s):
        """
        fromScript(s) -> True if succeeded, False otherwise.

        Initialise from script s.
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

    def notDefault(self,):
        """
        notDefault() -> True if set to its default value, False otherwise.
        """
        return bool()