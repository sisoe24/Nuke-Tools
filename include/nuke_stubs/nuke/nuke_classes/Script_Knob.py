from numbers import Number
from typing import *

import nuke
from . import *

class Script_Knob(String_Knob):
    """
    A button which executes a TCL script.
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

    def command(self,):
        """
        self.command() -> str

        Get the current command.
        @return: The current command as a string, or None if there is no current command.
        """
        return str()

    def value(self,):
        """
        self.value() -> str

        Get the current command.
        @return: The current command as a string, or None if there is no current command.
        """
        return str()

    def setCommand(self, cmd:str):
        """
        self.setCommand(cmd) -> None
        Set the new command for this knob.
        @param cmd: String containing a TCL command.
        @return: None.
        """
        return None

    def setValue(self, cmd:str):
        """
        self.setValue(cmd) -> None
        Set the new command for this knob.
        @param cmd: String containing a TCL command.
        @return: None.
        """
        return None

    def execute(self,):
        """
        self.execute() -> None
        Execute the command.
        @return: None.
        """
        return None