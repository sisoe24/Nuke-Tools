from numbers import Number
from typing import *

import nuke
from . import *

class Panel(object):
    """
    Panel
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

    def width(self,):
        """
        self.width() -> The width as an int.
        Get the width of the panel.
        @return: The width as an int.
        """
        return int()

    def setWidth(self, val:int):
        """
        self.setWidth(val) -> True if successful.
        Set the width of the panel.
        @param val: The width as an int.
        @return: True if successful.
        """
        return bool()

    def title(self,):
        """
        self.title() -> The title as a string.
        Get the current title for the panel.
        @return: The title as a string.
        """
        return str()

    def setTitle(self, val:str):
        """
        self.setTitle(val) -> True if successful.
        Set the current title for the panel.
        @param val: The title as a string.
        @return: True if successful.
        """
        return bool()

    def addSingleLineInput(self, name:str, value:Any):
        """
        self.addSingleLineInput(name, value) -> True if successful.
        Add a single-line input knob to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addPasswordInput(self, name:str, value:Any):
        """
        self.addPasswordInput(name, value) -> True if successful.
        Add a password input knob to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addFilenameSearch(self, name:str, value:Any):
        """
        self.addFilenameSearch(name, value) -> True if successful.
        Add a filename search knob to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addClipnameSearch(self, name:str, value:Any):
        """
        self.addClipnameSearch(name, value) -> True if successful.
        Add a clipname search knob to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addMultilineTextInput(self, name:str, value:Any):
        """
        self.addMultilineTextInput(name, value) -> True if successful.
        Add a multi-line text knob to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addNotepad(self, name:str, value:Any):
        """
        self.addNotepad(name, value) -> True if successful.
        Add a text edit widget to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addBooleanCheckBox(self, name:str, value:Any):
        """
        self.addBooleanCheckBox(name, value) -> True if successful.
        Add a boolean check box knob to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addRGBColorChip(self, name:str, value:Any):
        """
        self.addRGBColorChip(name, value) -> True if successful.
        Add a color chooser to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addEnumerationPulldown(self, name:str, value:Any):
        """
        self.addEnumerationPulldown(name, value) -> True if successful.
        Add a pulldown menu to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addTextFontPulldown(self, name:str, value:Any):
        """
        self.addTextFontPulldown(name, value) -> True if successful.
        Add a font chooser to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addExpressionInput(self, name:str, value:Any):
        """
        self.addExpressionInput(name, value) -> True if successful.
        Add an expression evaluator to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addScriptCommand(self, name:str, value:Any):
        """
        self.addScriptCommand(name, value) -> True if successful.
        Add a script command evaluator to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def addButton(self, name:str, value:Any):
        """
        self.addButton(name, value) -> True if successful.
        Add a button to the panel.
        @param name: The name for the new knob.
        @param value: The initial value for the new knob.
        @return: True if successful.
        """
        return bool()

    def value(self, name:str):
        """
        self.value(name) -> The value for the field if any, otherwise None.
        Get the value of a particular control in the panel.
        @param name: The name of the knob to get a value from.
        @return: The value for the field if any, otherwise None.
        """
        return Any

    def execute(self, name:str):
        """
        self.execute(name) -> The result of the script as a string, or None if it fails.
        Execute the script command associated with a particular label and return the result as a string.
        @param name: The name of the script field to execute.
        @return: The result of the script as a string, or None if it fails.
        """
        return str()

    def clear(self,):
        """
        self.clear() -> None
        Clear all panel attributes.
        """
        return None

    def show(self,):
        """
        self.show() -> An int value indicating how the dialog was closed (normally, or cancelled).
        Display the panel.
        @return: An int value indicating how the dialog was closed (normally, or cancelled).
        """
        return int()

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None