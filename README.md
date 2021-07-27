# nuke-tools README

A bunch of Nuke related operations that will facilitate writing code for Nuke.

> This is a companion extension for: www.tutut.com. Without the plugin, this extension will not work.

## Installation

dunno really try

## Features

* Execute code inside Nuke from a machine in your local network.
  * When used locally (same machine) no configuration is required by user, just running the server inside Nuke.
  * Specify a custom address when connection is from/to another computer.
  * Multiple computer can connect to the same Nuke instance.
* Get output of Nuke execution inside Visual Studio Code.
* Easy commands for creating a Nuke instance via the terminal with default or optional arguments.

![execute code](/images/execute_code.gif)

## Available Commands

All commands are Available by opening the Command Palette (`Command+Shift+P` on macOS and `Ctrl+Shift+P` on Windows/Linux) and typing in one of the following:

| Command                                    | Description                                     | Shortcut      |
| ------------------------------------------ | ----------------------------------------------- | ------------- |
| `Nuke: Launch main executable`             | Launch main executable                          | `alt+shift+n` |
| `Nuke: Launch alternative executable`      | Launch alternative executable                   |               |
| `Nuke: Launch main executable with prompt` | Launch main exec. with prompt for optional args |               |
| `Nuke: Run Inside Nuke`                    | Execute python code inside nuke                 | `alt+shift+r` |
| `Nuke: Show Network Addresses`             | Show network addresses                          |               |

Every command can be re-assigned to a new shortcut. (see [docs](https://code.visualstudio.com/docs/getstarted/keybindings) for more info)

`Nuke: Run Inside Nuke` can be access also via a button in the Editor Toolbar or the right click context menu.

## Extension Settings

### `nukeTools.nukeExecutable.primaryExecutablePath`

Primary path for the Nuke executable. **Note**: on MacOS is the file inside Show Package Contents -> Contents/MacOS/NukeXX

### `nukeTools.nukeExecutable.secondaryExecutablePath`

Same as primary executable. Could be a different Nuke version.

### `nukeTools.nukeExecutable.options.defaultCommandLineArguments`

Command line arguments to be added at each "Nuke launch" 🚀.

### `nukeTools.nukeExecutable.options.restartInstance`

Restart the terminal instance instead of creating new ones. **Use with caution** as this option will terminate every Nuke process created by the extension. Useful when rapid testing GUI plugins and don't need to save the Nuke comp. 

### `nukeTools.other.clearPreviousOutput`

Clear previous console output before next code execution.

### `nukeTools.network.enableManualConnection`

If enabled, `nukeTools.network.port` and `nukeTools.network.host` will take over the default settings. Useful when connecting to/from another computer.

### `nukeTools.network.port`

Specify a different port for the connection. This will not work if `#nukeTools.network.enableManualConnection#` is not enabled. Server address should be taken from the Nuke plugin.

### `nukeTools.network.host`

Same as `nukeTools.network.port`. Host could be the localhost or the local ip.

## Known Issues

The extension has been tested only on a small amount of simple scripts, so if you encounter any errors feel free to pm or file a bug report with a testable sample of your code.

## Release Notes

### [Unreleased]

* Create PySide2 startup template.

### [0.0.1]

Initial release of Nuke Tools
