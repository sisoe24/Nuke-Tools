from numbers import Number
from typing import *

import nuke
from . import *

class LookupCurves_Knob(Knob):
    """
    Provide a set of user-editable lookup curves.
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

    def addCurve(self, curve:str, expr=None):
        """
        self.addCurve(curve, expr=None) -> None
        Adds a curve.
        @param curve: The name of an animation curve, or an AnimationCurve instance.
        @param expr: Optional parameter giving an expression for the curve.
        @return: None
        """
        return None

    def editCurve(self, curve:str, expr=None):
        """
        self.editCurve(curve, expr=None) -> None
        Edits an existing curve.
        @param curve: The name of an animation curve.
        @param expr: The new expression for the curve.
        @return: None
        """
        return None

    def delCurve(self, curve:str):
        """
        self.delCurve(curve) -> None
        Deletes a curve.
        @param curve: The name of the animation curve.
        @return: None
        """
        return None