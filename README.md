# Nuke Tools README

A bunch of Nuke related operations that will facilitate writing code for Nuke.

> This is primarily a companion extension for: [NukeServerSocket](#nukeserversocket). Some features will only work when the server inside Nuke is active.

- [Nuke Tools README](#nuke-tools-readme)
  - [Features](#features)
  - [Nuke Python Stubs](#nuke-python-stubs)
  - [BlinkScript](#blinkscript)
  - [NukeServerSocket](#nukeserversocket)
  - [Available Commands](#available-commands)
  - [Extension Settings](#extension-settings)
    - [`nukeTools.nukeExecutable.primaryExecutablePath`](#nuketoolsnukeexecutableprimaryexecutablepath)
    - [`nukeTools.nukeExecutable.secondaryExecutablePath`](#nuketoolsnukeexecutablesecondaryexecutablepath)
    - [`nukeTools.nukeExecutable.options.defaultCommandLineArguments`](#nuketoolsnukeexecutableoptionsdefaultcommandlinearguments)
    - [`nukeTools.nukeExecutable.options.restartInstance`](#nuketoolsnukeexecutableoptionsrestartinstance)
    - [`nukeTools.other.clearPreviousOutput`](#nuketoolsotherclearpreviousoutput)
    - [`nukeTools.network.enableManualConnection`](#nuketoolsnetworkenablemanualconnection)
    - [`nukeTools.network.port`](#nuketoolsnetworkport)
    - [`nukeTools.network.host`](#nuketoolsnetworkhost)

## Features

* Execute code inside Nuke from a machine in your local network.
  * Get output of Nuke execution inside Visual Studio Code.
  * When used locally (same machine) no configuration is required by user, just running the server inside Nuke.
  * Specify a custom address when connection is from/to another computer.
  * Multiple computer can connect to the same Nuke instance.
  * BlinkScript support.
* Easy commands for launching Nuke instances via the terminal with default or optional arguments.
* Included Nuke Python Stubs to be added to `python.analysis.extraPaths` for a simple auto complete feature.

## Nuke Python Stubs

> The stubs are pre-generated and you can check more about the project [here](https://github.com/sisoe24/Nuke-Python-Stubs).

Nuke Tools now includes python stubs for Nuke.

The command `Add Stubs to Workspace` will add the stubs path to `python.analysis.extraPaths` of your workspace settings folder. 


Alternatively the stubs can be found inside the extension folder: `$HOME/.vscode/extensions/virgilsisoe.nuke-tools/Nuke-Python-Stubs/nuke_stubs`.

> Note: if you decide to add manually the stubs path to the global settings `python.analysis.extraPaths`, you should keep in mind that, if creating a `python.analysis.extraPaths` workspace settings, it will override the global one. The command `Add Stubs to Workspace` takes care of this by adding the workspace settings only if there is no global setting or the workspace has overwritten the global but it does not have the path.
> 
## BlinkScript

>  [NukeServerSocket](#nukeserversocket) >= 0.1.0 is needed in order for this to work.

You can execute code from the text editor directly inside a Nuke BlinkScript node.

The extension will take the name of the current active file and create a blinkscript node inside Nuke with the name as the current filename. If the node already exists then will only modified its source code. Once done will recompile the source kernel.

The accepted file extension are `.cpp` or `.blink`.

> There used to be an extension on the marketplace for the blink language syntax but it appears to have been taken down. If you want to use a .blink file, you could set the language id to C++ in order to have the syntax colored. Also the extension [Material Icon Theme](https://marketplace.visualstudio.com/items?itemName=PKief.material-icon-theme) offers a nice Nuke icon for the .blink files.

## NukeServerSocket

Download here the companion plugin for Nuke: [Git](https://github.com/sisoe24/NukeServerSocket), [Nukepedia](http://www.nukepedia.com/python/misc/nukeserversocket).

## Available Commands

All commands are Available by opening the Command Palette (`Command+Shift+P` on macOS and `Ctrl+Shift+P` on Windows/Linux) and typing in one of the following:

| Command                                    | Description                                     | Shortcut      |
| ------------------------------------------ | ----------------------------------------------- | ------------- |
| `Nuke: Launch main executable`             | Launch main executable                          | `alt+shift+n` |
| `Nuke: Launch alternative executable`      | Launch alternative executable                   |               |
| `Nuke: Launch main executable with prompt` | Launch main exec. with prompt for optional args |               |
| `Nuke: Run Inside Nuke`                    | Execute code inside nuke                        | `alt+shift+r` |
| `Nuke: Show Network Addresses`             | Show network addresses                          |               |
| `Nuke: Add Stubs to Workspace`             | Add Python stubs path to workspace              |               |

Every command can be re-assigned to a new shortcut. (see [docs](https://code.visualstudio.com/docs/getstarted/keybindings) for more info)

`Nuke: Run Inside Nuke` can be access also via a button in the Editor Toolbar or the right click context menu.

## Extension Settings

### `nukeTools.nukeExecutable.primaryExecutablePath`

Primary path for the Nuke executable.

* On MacOS you can find the file with: _Show Package Contents -> Contents/MacOS/Nuke..._
* On Windows WSL the path should be the Unix style: _/mnt/c/Program Files/..._

### `nukeTools.nukeExecutable.secondaryExecutablePath`

Same as primary executable. Could be a different Nuke version.

### `nukeTools.nukeExecutable.options.defaultCommandLineArguments`

Command line arguments to be added at each "Nuke launch" 🚀.

### `nukeTools.nukeExecutable.options.restartInstance`

Restart the terminal instance instead of creating new ones. **Use with caution** as this option will terminate every Nuke process created by the extension. Useful when rapid testing GUI plugins and don't need to save the Nuke comp.

### `nukeTools.other.clearPreviousOutput`

Clear previous console output before next code execution.

### `nukeTools.network.enableManualConnection`

If enabled, `nukeTools.network.port` and `nukeTools.network.host` will take over the default settings. Needed when connecting to/from another computer.

### `nukeTools.network.port`

Specify a different port for the connection. This will only work if `nukeTools.network.enableManualConnection` is enabled. Server address should be taken from the Nuke plugin.

### `nukeTools.network.host`

Same as `nukeTools.network.port`. Host could be the localhost or the local ip.
