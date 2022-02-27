from numbers import Number
from typing import *

import nuke
from . import *

class Channel_Knob(Knob):
    """
    A knob which lets you select a layer and enable or disable individual channels.
    self.__init__(s, label, depth) -> None
    Constructor.
    @param s: name.
    @param label: Optional name to appear in GUI. Defaults to the knob's name.
    @param depth: Optional number of channels with zero being the Nuke default number of channels. Defaults to 0.
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

    def layerSelector(self,):
        """
        self.layerSelector() -> bool
        """
        return bool()

    def channelSelector(self,):
        """
        self.channelSelector() -> bool
        """
        return bool()

    def checkMarks(self,):
        """
        self.checkMarks() -> bool
        """
        return bool()

    def isChannelEnabled(self, name:str):
        """
        self.isChannelEnabled(name) -> bool

        Test if a channel is enabled.
        @param name: The name of the channel.@return: True if the channel is enabled, False otherwise.
        """
        return bool()

    def enableChannel(self, name:str, b:bool):
        """
        self.enableChannel(name, b) -> None

        Enable or disable a channel.
        @param name: The name of the channel.
        @param b: True to enable the channel, False to disable it.
        @return: None
        """
        return None

    def setEnable(self, name:str):
        """
        self.setEnable(name) -> None

        Enable a channel.
        @param name: The name of the channel to enable.
        @return: None
        """
        return None

    def depth(self,):
        """
        self.depth() -> int

        Get the channel depth.
        @return: The depth of the channel as an int.
        """
        return int()

    def inputKnob(self,):
        """
        self.inputKnob() -> bool
        """
        return bool()

    def inputNumber(self,):
        """
        self.inputNumber() -> int
        """
        return int()

    def setInput(self, num:Number):
        """
        self.setInput(num) -> None
        Set the input number for this knob.@param num: The number of the new input.
        @return: None
        """
        return None

    def value(self,):
        """
        self.value() -> str
        Get the name of the selected channel.
        @return: The name of the channel as a string.
        """
        return str()

    def setValue(self, name:str):
        """
        self.setValue(name) -> None
        Set the selected channel using the channel name.
        @param name: The name of the new channel as a string.
        @return: None
        @raise ValueError exception if the channel doesn't exist.
        """
        return None