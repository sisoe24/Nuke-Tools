from numbers import Number
from typing import *

import nuke
from . import *

class MenuBar(object):
    """
    MenuBar
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def addCommand(self, name:str, command:str=None, shortcut:str=None, icon:str=None, tooltip:str=None, index:Number=None, readonly:bool=None):
        """
        self.addCommand(name, command, shortcut, icon, tooltip, index, readonly) -> The menu/toolbar item that was added to hold the command.
        Add a new command to this menu/toolbar. Note that when invoked, the command is automatically enclosed in an undo group, so that undo/redo functionality works. Optional arguments can be specified by name.
        Note that if the command argument is not specified, then the command will be auto-created as a "nuke.createNode()" using the name argument as the node to create.

        Example:
        menubar = nuke.menu('Nuke')
        fileMenu = menubar.findItem('File')
        fileMenu.addCommand('NewCommand', 'print 10', shortcut='t')

        @param name: The name for the menu/toolbar item. The name may contain submenu names delimited by '/' or '', and submenus are created as needed.
        @param command: Optional. The command to add to the menu/toolbar. This can be a string to evaluate or a Python Callable (function, method, etc) to run.
        @param shortcut: Optional. The keyboard shortcut for the command, such as 'R', 'F5' or 'Ctrl-H'. Note that this overrides pre-existing other uses for the shortcut.
        @param icon: Optional. An icon for the command. This should be a path to an icon in the nuke.pluginPath() directory. If the icon is not specified, Nuke will automatically try to find an icon with the name argument and .png appended to it.
        @param tooltip: Optional. The tooltip text, displayed on mouseover for toolbar buttons.
        @param index: Optional. The position to insert the new item in, in the menu/toolbar. This defaults to last in the menu/toolbar.
        @param readonly: Optional. True/False for whether the item should be available when the menu is invoked in a read-only context.
        @param shortcutContext: Optional. Sets the shortcut context (0==Window, 1=Application, 2=DAG).
        @return: The menu/toolbar item that was added to hold the command.
        """
        return Any

    def addMenu(self,**kwargs):
        """
        self.addMenu(**kwargs) -> The submenu that was added.
        Add a new submenu.
        @param **kwargs The following keyword arguments are accepted:
                        name      The name for the menu/toolbar item
                        icon      An icon for the menu. Loaded from the nuke search path.
                        tooltip   The tooltip text.
                        index     The position to insert the menu in. Use -1 to add to the end of the menu.
        @return: The submenu that was added.
        """
        return Any

    def clearMenu(self,):
        """
        self.clearMenu() 
        Clears a menu.
        @param **kwargs The following keyword arguments are accepted:
                        name      The name for the menu/toolbar item
        @return: true if cleared, false if menu not found 
        """
        return bool()

    def addSeparator(self,**kwargs):
        """
        self.addSeparator(**kwargs) -> The separator that was created.
        Add a separator to this menu/toolbar.
        @param **kwargs The following keyword arguments are accepted:
        index     The position to insert the new separator in, in the menu/toolbar.
        @return: The separator that was created.
        """
        return Any

    def findItem(self, name:str):
        """
        self.findItem(name) -> Menu or None
        Finds a submenu or command with a particular name.
        @param name: The name to search for.
        @return: The submenu or command we found, or None if we could not find anything.
        """
        return Union[Menu, None]

    def menu(self, name:str):
        """
        self.menu(name) -> Menu or None
        Finds a submenu or command with a particular name.
        @param name: The name to search for.
        @return: The submenu or command we found, or None if we could not find anything.
        """
        return Union[Menu, None]

    def removeItem(self, name:str):
        """
        self.removeItem(name) -> None
        Removes a submenu or command with a particular name. If the containing menu becomes empty, it will be removed too.
        @param name: The name to remove for.
        @return: true if removed, false if menu not found 
        """
        return None

    def items(self,):
        """
        self.items() -> None
        Returns a list of sub menu items.
        """
        return None

    def name(self,):
        """
        self.name() -> String
        Returns the name of the menu item.
        """
        return str()

    def addAction(self,action):
        """
        self.addAction(action) -> bool
        Adds the QAction to the menu.
        """
        return bool()

    def updateMenuItems(self,):
        """
        updateMenuItems() -> None
        Updates menu items' states. Call on about to show menu.
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None