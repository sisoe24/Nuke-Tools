from numbers import Number
from typing import *

import nuke
from . import *

class FreeType_Knob(Knob):
    """
    A knob which holds a font family and style name.
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

    def getValue(self,):
        """
        self.getValue() -> [String, String].
        Returns the font family/style on this knob.
        @return: [String, String].
        """
        return str()

    def setValue(self, family:str, style:str):
        """
        self.setValue(family,style) -> None.
        self.setValue(filename,index) -> None.
        Change font family/style with a new one.
        It raises an exception if the font is not available.
        @param family: String of the font family name.
        @param style: String of the font style name.
        @param filename: Font filename.
        @param index: Face index.
        @return: None.
        """
        return None