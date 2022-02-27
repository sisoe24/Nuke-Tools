from numbers import Number
from typing import *

import nuke
from . import *

class AnimationCurve(object):
    """
    AnimationCurve
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

    def size(self,):
        """
        self.size() -> Number of keys.
        @return: Number of keys.
        """
        return Number()

    def keys(self,):
        """
        self.keys() -> List of keys.
        @return: List of keys.
        """
        return list()

    def knobAndFieldName(self,):
        """
        self.knobAndFieldName() -> string.
        Knob and field name combined (e.g. 'translate.x').
        @return: string.
        """
        return str()

    def knob(self,):
        """
        self.knob() -> Knob.
        Return knob this animation belongs to.@return: Knob.
        """
        return Knob()

    def knobIndex(self,):
        """
        self.knobIndex() -> Int.
        Return the knob index this animation belongs to.@return: Int.
        """
        return int()

    def noExpression(self,):
        """
        self.noExpression() -> bool
        @return: True if the expression is the default expression (i.e. the keys
        control the curve), False otherwise.
        """
        return bool()

    def constant(self,):
        """
        self.constant() -> bool
        @return: True if the animation appears to be a horizontal line, is a simple
        number, or it is the default and all the points are at the same y value and
        have 0 slopes. False otherwise.
        """
        return bool()

    def identity(self,):
        """
        self.identity() -> bool
        @return: True if the animation appears to be such that y == x everywhere. This
        is True only for an expression of 'x' or the default expression and all points
        having y == x and slope == 1. Extrapolation is ignored.
        """
        return bool()

    def selected(self,):
        """
        self.selected() -> bool
        @return: True if selected, False otherwise.
        """
        return bool()

    def evaluate(self, t:Number):
        """
        self.evaluate(t) -> float
        Value at time 't'.
        @param t: Time.
        @return: The value of the animation at time 't'.
        """
        return float()

    def derivative(self, t:Number, n:int=None):
        """
        self.derivative(t, n) -> Float.
        The n'th derivative at time 't'. If n is less than 1 it returns evaluate(t).
        @param t: Time.
        @param n: Optional. Default is 1.
        @return: The value of the derivative.
        """
        return float()

    def inverse(self, y:Any):
        """
        self.inverse(y) -> Float.
        The inverse function at value y. This is the value of x such that evaluate(x)
        returns y.
        This is designed to invert color lookup tables. It only works if the
        derivative is zero or positive everywhere.
        @param y: The value of the function to get the inverse for.
        @return: Float.
        """
        return float()

    def integrate(self, t1:Number, t2:Number):
        """
        self.integrate(t1, t2) -> Float.
        Calculate the area underneath the curve from t1 to t2.
        @param t1 The start of the integration range.
        @param t2 The end of the integration range.
        @return: The result of the integration.
        """
        return float()

    def setKey(self, t:Number, y:Any):
        """
        self.setKey(t, y) -> Key.
        Set a key at time t and value y. If there is no key
        there one is created. If there is a key there it is moved
        vertically to be at y.  If a new key is inserted the
        interpolation and extrapolation are copied from a neighboring key, if
        there were no keys then it is set to nuke.SMOOTH interpolation and
        nuke.CONSTANT extrapolation.
        @param t: The time to set the key at.
        @param y: The value for the key.
        @return: The new key.
        """
        return Any

    def addKey(self, keys:Iterable):
        """
        self.addKey(keys) -> None.
        Insert a sequence of keys.
        @param keys: Sequence of AnimationKey.
        @return: None.
        """
        return None

    def clear(self,):
        """
        self.clear() -> None.
        Delete all keys.
        @return: None.
        """
        return None

    def setExpression(self, s:str):
        """
        self.setExpression(s) -> None.
        Set expression.
        @param s: A string containing the expression.
        @return: None.
        """
        return None

    def expression(self,):
        """
        self.expression() -> String.
        Get the expression.@return: String.
        """
        return str()

    def changeInterpolation(self, keys:Iterable, type):
        """
        self.changeInterpolation(keys, type) -> None.
        Change interpolation (and extrapolation) type for the keys.
        @param keys: Sequence of keys.
        @param type: Interpolation type. One of:
               nuke.HORIZONTAL
               nuke.BREAK
               nuke.BEFORE_CONST
               nuke.BEFORE_LINEAR
               nuke.AFTER_CONST
               nuke.AFTER_LINEAR.
        @return: None.
        """
        return None

    def fromScript(self, s:str):
        """
        self.fromScript(s) -> None.
        @param s: String.
        @return: None.
        """
        return None

    def toScript(self, selected:bool=None):
        """
        self.toScript(selected) -> str
        @param selected: Optional parameter. If this is given and is True, then only
        process the selected curves; otherwise convert all.
        @return: A string containing the curves.
        """
        return str()

    def fixSlopes(self,):
        """
        self.fixSlopes() -> None.
        @return: None.
        """
        return None

    def view(self,):
        """
        self.view() -> String.
        The view this AnimationCurve object is associated with.
        @return: String.
        """
        return str()

    def removeKey(self, keys:Iterable):
        """
        self.removeKey(keys) -> None.
        Remove some keys from the curve.
        @param keys: The sequence of keys to be removed.
        @return: None.
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None