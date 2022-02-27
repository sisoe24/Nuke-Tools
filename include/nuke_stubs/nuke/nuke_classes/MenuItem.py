from numbers import Number
from typing import *

import nuke
from . import *

class MenuItem(object):
    """
    MenuItem
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def setEnabled(self, enabled:bool, recursive:bool):
        """
        self.setEnabled(enabled, recursive) -> None
        Enable or disable the item.
        @param enabled: True to enable the object; False to disable it.
        @param recursive: True to also setEnabled on submenu actions.
        """
        return None

    def setVisible(self, visible:bool):
        """
        self.setVisible(visible) -> None
        Show or hide the item.
        @param visible: True to show the object; False to hide it.
        """
        return None

    def invoke(self,):
        """
        self.invoke() -> None
        Perform the action associated with this menu item.
        """
        return None

    def action(self,):
        """
        self.action() -> None
        Get the action associated with this menu item.
        """
        return None

    def name(self,):
        """
        self.name() -> String
        Returns the name of the menu item.
        """
        return str()

    def icon(self,):
        """
        self.icon() -> String
        Returns the name of the icon on this menu item as path of the icon.
        """
        return str()

    def setIcon(self, icon:str):
        """
        self.setIcon(icon) -> None
        Set the icon on this menu item.
        @param icon: the new icon as a path
        """
        return None

    def script(self,):
        """
        self.script() -> String
        Returns the script that gets executed for this menu item.
        """
        return str()

    def setScript(self,script):
        """
        self.setScript(script) -> None
        Set the script to be executed for this menu item.
        Note: To call a python script file, you can use the execfile() function. i.e:
        menu.setScript("execfile('script.py')")
        """
        return None

    def shortcut(self,):
        """
        self.shortcut() -> String
        Returns the keyboard shortcut on this menu item. The format of this is the PortableText format. It will return a string such as "Ctrl+Shift+P". Note that on Mac OS X the Command key is equivalent to Ctrl.
        """
        return str()

    def setShortcut(self, keySequence:str):
        """
        self.setShortcut(keySequence) -> None
        Set the keyboard shortcut on this menu item.
        @param keySequence: the new shortcut in PortableText format, e.g. "Ctrl+Shift+P"
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None