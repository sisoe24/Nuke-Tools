# 1. Nuke Tools README

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/b4124a14ccb4467b89ec8cd607b0d16f)](https://www.codacy.com/gh/sisoe24/Nuke-Tools/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sisoe24/Nuke-Tools&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/b4124a14ccb4467b89ec8cd607b0d16f)](https://www.codacy.com/gh/sisoe24/Nuke-Tools/dashboard?utm_source=github.com&utm_medium=referral&utm_content=sisoe24/Nuke-Tools&utm_campaign=Badge_Coverage)
[![DeepSource](https://deepsource.io/gh/sisoe24/Nuke-Tools.svg/?label=active+issues&show_trend=true&token=HEB3mg6EWSs71ckagYV0_P2u)](https://deepsource.io/gh/sisoe24/Nuke-Tools/?ref=repository-badge)

[![Download](https://img.shields.io/badge/Marketplace-Download-blue)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools)
[![Version](https://img.shields.io/visual-studio-marketplace/v/virgilsisoe.nuke-tools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools&ssr=false#version-history)
[![Installs](https://img.shields.io/visual-studio-marketplace/i/virgilsisoe.nuke-tools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools)
[![Ratings](https://img.shields.io/visual-studio-marketplace/r/virgilsisoe.nuke-tools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools&ssr=false#review-details)
[![vscode](https://img.shields.io/visual-studio-marketplace/last-updated/virgilsisoe.nuke-tools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools)

A bunch of Nuke related tools that will help the development process in Visual Studio Code.

- [1. Nuke Tools README](#1-nuke-tools-readme)
  - [1.1. Features](#11-features)
  - [1.2. Requirements](#12-requirements)
  - [1.3. Usage](#13-usage)
  - [1.4. BlinkScript](#14-blinkscript)
  - [1.5. Available Commands](#15-available-commands)
  - [1.6. Extension Settings](#16-extension-settings)

## 1.1. Features

- Execute code inside Nuke from a machine in your local network.
  - Get output of Nuke execution inside Visual Studio Code.
  - When used locally (same machine) no configuration is required, just running the server inside Nuke.
  - Specify a custom address when connection is from/to another computer.
  - BlinkScript support.
- Included Nuke Python Stubs to be added to `python.analysis.extraPaths` for a simple auto complete feature.
- Convenient commands for launching Nuke instances via the terminal with default or optional arguments.

## 1.2. Requirements

This extension is primarily a companion for *NukeServerSocket*. Executing code will only work when the plugin is up and running inside Nuke.

## 1.3. Usage

To execute code:

1. Download and install the companion plugin NukeServerSocket:
   - Via the Command Palette: `Nuke: Add NukeServerSocket` (more info on [Available Commands](#15-available-commands)).
   - [Github](https://github.com/sisoe24/NukeServerSocket/releases)
   - [Nukepedia](http://www.nukepedia.com/python/misc/nukeserversocket)
2. Connect NukeServerSocket inside Nuke.
3. With an active Python/BlinkScript file, use the command `Nuke: Run Inside Nuke` from the Command Palette or use the dedicated button in the editor top right corner.

![CodeExecution](/images/execute_code.gif)

To use the Python stubs

1. Use the command `Nuke: Add Python Stubs` to add the stubs to your `python.analysis.extraPaths` setting.
2. Write `import nuke` into your script.

![PythonStubs](/images/auto_complete.gif)

> NOTE: Having a package named `nuke` in your workspace root, might cause problems for the suggestions.

## 1.4. BlinkScript

> NOTE: BlinkScript features are available in a basic form. If you would like to see something more, feel free to make a request or open a PR. Also check out [Material Icon Theme](https://marketplace.visualstudio.com/items?itemName=PKief.material-icon-theme) that adds a Nuke icon for the .blink file.

- Features
  - Code execution.
  - Syntax highlighting.
  - Code formatting.
  - Simple code suggestion.
  - Startup saturation snippet.

- Execute BlinkScript

  The extension will create a blinkscript node named after the current active file.
  If the node already exists, then it will only modified the code and recompile it.

  The accepted file extension code are `.cpp` or `.blink`.

## 1.5. Available Commands

- All commands are available by opening the Command Palette (`Command+Shift+P` on macOS and `Ctrl+Shift+P` on Windows/Linux) and typing in one of the following Command Name:

| Command Name                               | Command ID                        | Description                                              |
| ------------------------------------------ | --------------------------------- | -------------------------------------------------------- |
| `Nuke: Launch main executable`             | `nuke-tools.launchNuke`           | Launch main executable                                   |
| `Nuke: Launch alternative executable`      | `nuke-tools.launchNukeAlt`        | Launch alternative executable                            |
| `Nuke: Launch main executable with prompt` | `nuke-tools.launchNukeOptArgs`    | Launch main exec. with prompt for optional args          |
| `Nuke: Run Inside Nuke`                    | `nuke-tools.runCodeInsideNuke`    | Execute code inside Nuke                                 |
| `Nuke: Add Stubs to Workspace`             | `nuke-tools.addPythonStubs`       | Add stubs path to workspace settings                     |
| `Nuke: Add NukeServerSocket`               | `nuke-tools.addNukeServerSocket`  | Add NukeServerSocket plugin to `.nuke` dir and `menu.py` |
| `Nuke: Show Network Addresses`             | `nuke-tools.showNetworkAddresses` | Show network addresses                                   |
| `Nuke: Debug Message`                      | `nuke-tools.testRunInsideNuke`    | Quick test connection                                    |

- `Nuke: Run Code Inside Nuke` can be access also via a button in the Editor Toolbar.
- `Nuke: Add NukeServerSocket` will copy the plugin folder inside `$HOME/.nuke` and append
an import statement inside the `menu.py` file: `import NukeServerSocket`. If `menu.py` does not exists, it will be created.
- By default the extension does not provide any shortcut, but every command can be assigned to one. (see [Key Bindings for Visual Studio Code](https://code.visualstudio.com/docs/getstarted/keybindings) for more information).

  Example `keybindings.json`:

  ```json
  [
      {
          "key":"alt+shift+n",
          "command":"nuke-tools.launchNuke",
      },
      {
          "key":"alt+shift+r",
          "command":"nuke-tools.runCodeInsideNuke",
          "when": "editorTextFocus"
      }
  ]
  ```

## 1.6. Extension Settings

- `nukeTools.nukeExecutable.primaryExecutablePath`: `string`

  Primary path for the Nuke executable.

  - On MacOS you can find the file with: *Show Package Contents -> Contents/MacOS/Nuke...*
  - On Windows WSL the path should be the Unix style: */mnt/c/Program Files/...*

- `nukeTools.nukeExecutable.secondaryExecutablePath`: `string`

  Same as primary executable. Could be a different Nuke version.

- `nukeTools.nukeExecutable.options.defaultCommandLineArguments`: `string`

  Command line arguments to be added at each "Nuke launch" 🚀.

- `nukeTools.nukeExecutable.options.restartInstance`: `boolean`

  Restart the terminal instance instead of creating new ones. **Use with caution** as this option will terminate every Nuke process created by the extension. Useful when rapid testing GUI plugins that don't need saving the composition.

- `nukeTools.other.clearPreviousOutput`: `boolean`

  Clear previous console output before next code execution.

- `nukeTools.other.showToolbarButton`: `boolean`

  Show the execute code button in the editor toolbar.

- `nukeTools.network.enableManualConnection`: `boolean`

  If enabled, `nukeTools.network.port` and `nukeTools.network.host` will take over the default settings. Needed when connecting to another computer.

  - `nukeTools.network.port`: `string`

    Specify a different port for the connection. This will only work if `nukeTools.network.enableManualConnection` is enabled. Server address should be taken from the Nuke plugin.

  - `nukeTools.network.host`: `string`

    Same as the port. Host could be the localhost or the local ip.

- `nukeTools.network.debug`: `boolean`

  Show network debug information in the output window. Enabling this option, will prevent the console from being cleared after code execution.
