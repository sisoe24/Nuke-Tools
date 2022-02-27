from numbers import Number
from typing import *

import nuke
from . import *

class String_Knob(Knob):
    """
    A knob which holds a string value. Appears as a text entry field in a Node panel.
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

    def getText(self, oc=None):
        """
        self.getText(oc) -> string

        Get the non-evaluated value of this knob - also see `value()`
        @param oc: Optional parameter specifying the output context.
        Return text associated with knob.
        """
        return str()

    def setValue(self, val:Any, view='default'):
        """
        self.setValue(val, view='default') -> None

        Set value of knob.
        @param val: The new value.
        @param view: Optional parameter specifying which view to set the value for. If omitted, the value will be set for the default view.
        @return: None
        """
        return None

    def value(self, oc=None):
        """
        self.value(oc) -> str

        Get the evaluated value of this knob as a string - also see `getText()`.
        @param oc: Optional parameter specifying the output context.
        @return: String value.
        """
        return str()

    def value(self, oc=None):
        """
        self.value(oc) -> str

        Get the evaluated value of this knob as a string - also see `getText()`.
        @param oc: Optional parameter specifying the output context.
        @return: String value.
        """
        return str()

    def setValue(self, val:Any, view='default'):
        """
        self.setValue(val, view='default') -> None

        Set value of knob.
        @param val: The new value.
        @param view: Optional parameter specifying which view to set the value for. If omitted, the value will be set for the default view.
        @return: None
        """
        return None

    def splitView(self, view=None):
        """
        self.splitView(view) -> None.
        Split the view away from the current knob value.
        @param view: Optional view. Default is current view.
        @return: None.
        """
        return None

    def unsplitView(self, view=None):
        """
        self.unsplitView(view) -> None.
        Unsplit the view so that it shares a value with other views.
        @param view: Optional view. Default is current view.
        @return: None.
        """
        return None