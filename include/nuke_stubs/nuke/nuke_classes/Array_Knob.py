from numbers import Number
from typing import *

import nuke
from . import *

class Array_Knob(Knob):
    """
    A knob which holds an array of values.
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

    def vect(self,):
        """
        self.vect() -> List of knob values.
        @return: List of knob values.
        Should only be used for knobs that are neither animated
        nor get their values from a ValueProvider.
        For knobs like that, use Array_Knob.getValue, instead
        """
        return list()

    def array(self,):
        """
        self.array() -> List of knob values.
        @return: List of knob values.
        Should only be used for knobs that are neither animated
        nor get their values from a ValueProvider.
        For knobs like that, use Array_Knob.getValue, instead
        """
        return list()

    def width(self,):
        """
        self.width() -> Width of array of values.
        @return: Width of array of values.
        """
        return list()

    def height(self,):
        """
        self.height() -> Height of array of values.
        @return: Height of array of values.
        """
        return list()

    def arraySize(self,):
        """
        self.arraySize() -> Number of elements in array.
        @return: Number of elements in array.
        """
        return list()

    def dimensions(self,):
        """
        self.dimensions() -> Dimensions in array.
        @return: Dimensions in array.
        """
        return list()

    def resize(self, w:Number, h:Number=None):
        """
        self.resize(w, h) -> True if successful, False otherwise.
        Resize the array.
        @param w: New width
        @param h: Optional new height
        @return: True if successful, False otherwise.
        """
        return bool()

    def fromScript(self, s:str):
        """
        self.fromScript(s) -> True if successful, False otherwise.
        Set value of the knob to a user defined script (TCL syntax, as in .nk file). Return True if successful.
        @param s: Nuke script to be set on knob.
        @return: True if successful, False otherwise.
        """
        return bool()

    def toScript(self, quote:bool=None, context:str=None):
        """
        self.toScript(quote, context) -> String.
        Return the value of the knob in script syntax.
        @param quote: Optional, default is False. Specify True to return the knob value quoted in {}.
        @param context: Optional context, default is current, None will be "contextless" (all views, all keys) as in a .nk file.
        @return: String.
        """
        return str()

    def notDefault(self,):
        """
        self.notDefault() -> True if any of the values is not set to the default, False otherwise.
        @return: True if any of the values is not set to the default, False otherwise.
        """
        return bool()

    def defaultValue(self,):
        """
        self.defaultValue() -> Default value.
        @return: Default value.
        """
        return Any

    def setDefaultValue(self, s:Iterable):
        """
        self.setDefaultValue(s) -> None.
        @param s: Sequence of floating-point values.
        @return: None.
        """
        return None

    def min(self,):
        """
        self.min() -> Minimum value.
        @return: Minimum value.
        """
        return Number()

    def min(self,):
        """
        self.min() -> Minimum value.
        @return: Minimum value.
        """
        return Number()

    def max(self,):
        """
        self.max() -> Maximum value.
        @return: Maximum value.
        """
        return Number()

    def max(self,):
        """
        self.max() -> Maximum value.
        @return: Maximum value.
        """
        return Number()

    def setRange(self, f1:Number, f2:Number):
        """
        self.setRange(f1, f2) -> None.
        Set range of values.
        @param f1 Min value.
        @param f2 Max value.
        @return: None.
        """
        return None

    def singleValue(self, view=None):
        """
        self.singleValue(view) -> True if holds a single value.
        @param view: Optional view. Default is current view.
        @return: True if holds a single value.
        """
        return bool()

    def setSingleValue(self, b:bool, view=None):
        """
        self.setSingleValue(b, view) -> None.
        Set to just hold a single value or not.
        @param b: Boolean object.
        @param view: Optional view. Default is current view.
        @return: None.
        """
        return None

    def frame(self,):
        """
        self.frame() -> Frame number.
        @return: Frame number.
        """
        return Number()

    def setValue(self, value:float, index:int=None, time:Number=None, view=None):
        """
        self.setValue(value, index, time, view) -> True if value changed, False otherwise. Safe to ignore.
        Set index to value at time and view.
        @param value: Floating point value.
        @param index: Optional index.
        @param time: Optional time.
        @param view: Optional view.
        @return: True if value changed, False otherwise. Safe to ignore.
        """
        return bool()

    def setValueAt(self, value:float, time:Number, index:int=None, view=None):
        """
        self.setValueAt(value, time, index, view) -> bool.
        Set value of element 'index' at time for view. If the knob is animated, it will set a new keyframe or change an existing one. Index and view are optional. Return True if successful.
        @param value: Floating point value.
        @param time: Time.
        @param index: Optional index.
        @param view: Optional view.
        @return: True if value changed, False otherwise. Safe to ignore.
        """
        return bool()

    def value(self, index:int=None, view=None, time:Number=None):
        """
        self.value(index, view, time) -> Floating point or List of floating point values (in case some are different).
        @param index: Optional index. Default is 0.
        @param view: Optional view.
        @param time: Optional time.
        @return: Floating point or List of floating point values (in case some are different).
        """
        return list()

    def value(self, index:int=None, view=None, time:Number=None):
        """
        self.value(index, view, time) -> Floating point or List of floating point values (in case some are different).
        @param index: Optional index. Default is 0.
        @param view: Optional view.
        @param time: Optional time.
        @return: Floating point or List of floating point values (in case some are different).
        """
        return list()

    def valueAt(self, time:Number, index:int=None, view=None):
        """
        self.valueAt(time, index, view) -> Floating point or List of floating point values (in case some are different).
        Return value for this knob at specified time, optional index and view.
        @param time: Time.
        @param index: Optional index. Default is 0.
        @param view: Optional view.
        @return: Floating point or List of floating point values (in case some are different).
        """
        return list()

    def valueAt(self, time:Number, index:int=None, view=None):
        """
        self.valueAt(time, index, view) -> Floating point or List of floating point values (in case some are different).
        Return value for this knob at specified time, optional index and view.
        @param time: Time.
        @param index: Optional index. Default is 0.
        @param view: Optional view.
        @return: Floating point or List of floating point values (in case some are different).
        """
        return list()

    def setKeyAt(self, time:Number, index:int=None, view=None):
        """
        self.setKeyAt(time, index, view) -> None.
        Set a key on element 'index', at time and view.
        @param time: Time.
        @param index: Optional index.
        @param view: Optional view.
        @return: None.
        """
        return None

    def removeKey(self, index:int=None, view=None):
        """
        self.removeKey(index, view) -> True if succeeded, False otherwise.
        Remove key.
        @param index: Optional index.
        @param view: Optional view.
        @return: True if succeeded, False otherwise.
        """
        return bool()

    def removeKeyAt(self, time:Number, index:int=None, view=None):
        """
        self.removeKeyAt(time, index, view) -> True if succeeded, False otherwise.
        Remove keyframe at specified time, optional index and view. Return True if successful.
        @param time: Time.
        @param index: Optional index.
        @param view: Optional view.
        @return: True if succeeded, False otherwise.
        """
        return bool()

    def isKey(self, index:int=None, view=None):
        """
        self.isKey(index, view) -> True if succeeded, False otherwise.
        @param index: Optional index.
        @param view: Optional view.
        @return: True if succeeded, False otherwise.
        """
        return bool()

    def isKeyAt(self, time:Number, index:int=None, view=None):
        """
        self.isKeyAt(time, index, view) -> True if succeeded, False otherwise.
        Returns True if there is a keyframe at specified time, optional index and view, otherwise returns False.
        @param time: Time.
        @param index: Optional index.
        @param view: Optional view.
        @return: True if succeeded, False otherwise.
        """
        return bool()

    def getNumKeys(self,*args, **kwargs):
        """
        Return number of keys at channel 'c'.
        """
        return None

    def getKeyIndex(self,*args, **kwargs):
        """
        Return index of the keyframe at time 't' and channel 'c'.
        """
        return None

    def getKeyTime(self,*args, **kwargs):
        """
        Return time of the keyframe at time 't' and channel 'c'.
        """
        return None

    def getDerivative(self,*args, **kwargs):
        """
        Return derivative at time 't' and index 'i'.
        """
        return None

    def getNthDerivative(self,*args, **kwargs):
        """
        Return n'th derivative at time 't' and index 'i'.
        """
        return None

    def getIntegral(self,*args, **kwargs):
        """
        Return integral at time interval [t1, t2] and index 'i'.
        """
        return None

    def setAnimated(self, index:int=None, view=None):
        """
        self.setAnimated(index, view) -> True if succeeded, False otherwise.
        Create an Animation object. Return True if successful, in which case caller must initialise it by calling setValue() or setValueAt().
        @param index: Optional index.
        @param view: Optional view.
        @return: True if succeeded, False otherwise.
        """
        return bool()

    def isAnimated(self, index:int=None, view=None):
        """
        self.isAnimated(index, view) -> True if animated, False otherwise.
        @param index: Optional index.
        @param view: Optional view.
        @return: True if animated, False otherwise.
        """
        return bool()

    def clearAnimated(self, index:int=None, view=None):
        """
        self.clearAnimated(index, view) -> True if succeeded, False otherwise.
        Delete animation.
        @param index: Optional index.
        @param view: Optional view.
        @return: True if succeeded, False otherwise.
        """
        return bool()

    def setExpression(self, expression:str, channel=-1, view=None):
        """
        self.setExpression(expression, channel=-1, view=None) -> bool
        Set the expression for a knob. You can optionally specify a channel to set the expression for.

        @param expression: The new expression for the knob. This should be a string.
        @param channel: Optional parameter, specifying the channel to set the expression for. This should be an integer.
        @param view: Optional view parameter. Without, this command will set the expression for the current view theinterface is displaying. Can be the name of the view or the index.
        @return: True if successful, False if not.
        """
        return bool()

    def hasExpression(self, index:int=None):
        """
        self.hasExpression(index) -> True if has expression, False otherwise.
        @param index: Optional index.
        @return: True if has expression, False otherwise.
        """
        return bool()

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

    def animations(self, view=None):
        """
        self.animations(view) -> AnimationCurve list.
        @param view: Optional view.
        @return: AnimationCurve list.
        Example:
        b = nuke.nodes.Blur()
        k = b['size']
        k.setAnimated(0)
        a = k.animations()
        a[0].setKey(0, 11)
        a[0].setKey(10, 20)
        """
        return list()

    def animation(self, chan, view=None):
        """
        self.animation(chan, view) -> AnimationCurve or None.
        Return the AnimationCurve for the  channel 'chan' and view 'view'. The view argument is optional.
        @param channel: The channel index.
        @param view: Optional view.
        @return: AnimationCurve or None.
        """
        return Union[AnimationCurve, None]

    def deleteAnimation(self, curve):
        """
        self.deleteAnimation(curve) -> None. Raises ValueError if not found.
        Deletes the AnimationCurve.
        @param curve: An AnimationCurve instance which belongs to this Knob.
        @return: None. Raises ValueError if not found.
        """
        return Any

    def copyAnimation(self, channel:int, curve, view=None):
        """
        self.copyAnimation(channel, curve, view) -> None.
        Copies the i'th channel of the AnimationCurve curve to this object. The view is optional and defaults to the current view.
        @param channel: The channel index.
        @param curve: AnimationCurve.
        @param view: Optional view. Defaults to current.
        @return: None.
        """
        return None

    def copyAnimations(self, curves:list, view=None):
        """
        self.copyAnimations(curves, view) -> None.
        Copies the AnimationCurves from curves to this object. The view is optional and defaults to the current view.
        @param curves: AnimationCurve list.
        @param view: Optional view. Defaults to current.
        @return: None.
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None