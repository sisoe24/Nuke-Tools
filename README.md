# 1. Nuke Tools README

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/b4124a14ccb4467b89ec8cd607b0d16f)](https://www.codacy.com/gh/sisoe24/Nuke-Tools/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sisoe24/Nuke-Tools&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/b4124a14ccb4467b89ec8cd607b0d16f)](https://www.codacy.com/gh/sisoe24/Nuke-Tools/dashboard?utm_source=github.com&utm_medium=referral&utm_content=sisoe24/Nuke-Tools&utm_campaign=Badge_Coverage)
[![DeepSource](https://deepsource.io/gh/sisoe24/Nuke-Tools.svg/?label=active+issues&show_trend=true&token=HEB3mg6EWSs71ckagYV0_P2u)](https://deepsource.io/gh/sisoe24/Nuke-Tools/?ref=repository-badge)

[![vscode](https://img.shields.io/visual-studio-marketplace/v/virgilsisoe.nuke-tools)](https://img.shields.io/visual-studio-marketplace/last-updated/virgilsisoe.nuke-tools)
[![vscode](https://img.shields.io/visual-studio-marketplace/last-updated/virgilsisoe.nuke-tools)](https://img.shields.io/visual-studio-marketplace/last-updated/virgilsisoe.nuke-tools)
[![Installs](https://img.shields.io/visual-studio-marketplace/i/virgilsisoe.nuke-tools)](https://deepsource.io/gh/sisoe24/Nuke-Tools/?ref=repository-badge)
[![Installs](https://img.shields.io/visual-studio-marketplace/r/virgilsisoe.nuke-tools)](https://deepsource.io/gh/sisoe24/Nuke-Tools/?ref=repository-badge)

A bunch of Nuke related tools that will help the development process in Visual Studio Code.

> This is primarily a companion extension for: [NukeServerSocket](#16-nukeserversocket). Some features will only work when the server inside Nuke is active.

- [1. Nuke Tools README](#1-nuke-tools-readme)
  - [1.1. NukeServerSocket](#11-nukeserversocket)
  - [1.2. Features](#12-features)
  - [1.3. Nuke Python Stubs](#13-nuke-python-stubs)
    - [1.3.1. Other ways to add the stubs](#131-other-ways-to-add-the-stubs)
  - [1.4. BlinkScript](#14-blinkscript)
    - [1.4.1. Features](#141-features)
    - [1.4.2. Execute BlinkScript](#142-execute-blinkscript)
  - [1.5. Available Commands](#15-available-commands)
  - [1.6. Extension Settings](#16-extension-settings)
    - [1.6.1. `nukeTools.nukeExecutable.primaryExecutablePath`](#161-nuketoolsnukeexecutableprimaryexecutablepath)
    - [1.6.2. `nukeTools.nukeExecutable.secondaryExecutablePath`](#162-nuketoolsnukeexecutablesecondaryexecutablepath)
    - [1.6.3. `nukeTools.nukeExecutable.options.defaultCommandLineArguments`](#163-nuketoolsnukeexecutableoptionsdefaultcommandlinearguments)
    - [1.6.4. `nukeTools.nukeExecutable.options.restartInstance`](#164-nuketoolsnukeexecutableoptionsrestartinstance)
    - [1.6.5. `nukeTools.other.clearPreviousOutput`](#165-nuketoolsotherclearpreviousoutput)
    - [1.6.6. `nukeTools.network.enableManualConnection`](#166-nuketoolsnetworkenablemanualconnection)
    - [1.6.7. `nukeTools.network.port`](#167-nuketoolsnetworkport)
    - [1.6.8. `nukeTools.network.host`](#168-nuketoolsnetworkhost)
    - [1.6.9. `nukeTools.network.debug`](#169-nuketoolsnetworkdebug)
  - [1.7. Overview](#17-overview)

## 1.1. NukeServerSocket

Download companion plugin:

- [Git](https://github.com/sisoe24/NukeServerSocket/releases)
- [Nukepedia](http://www.nukepedia.com/python/misc/nukeserversocket)

## 1.2. Features

- Execute code inside Nuke from a machine in your local network.
  - Get output of Nuke execution inside Visual Studio Code.
  - When used locally (same machine) no configuration is required, just running the server inside Nuke.
  - Specify a custom address when connection is from/to another computer.
  - Multiple computer can connect to the same Nuke instance.
  - BlinkScript support.
- Easy commands for launching Nuke instances via the terminal with default or optional arguments.
- Included Nuke Python Stubs to be added to `python.analysis.extraPaths` for a simple auto complete feature.

## 1.3. Nuke Python Stubs

> The stubs are pre-generated and you can check more about the github project [here](https://github.com/sisoe24/Nuke-Python-Stubs).

Nuke Tools now includes python stubs for Nuke.

For the most part, stubs files will have the type annotation declared. This will allow vscode to infer the type of the variable. Some of them are wrong or missing but you can read more about that in the git repo.

The command `Add Python Stubs` will add the stubs path to your workspace `python.analysis.extraPaths` settings.
Then is simple as: `import nuke`

> If you have a package named `nuke` in your workspace root, it will not work, as python will import that one first.

### 1.3.1. Other ways to add the stubs

The stubs can be found inside the extension folder: `$HOME/.vscode/extensions/virgilsisoe.nuke-tools/Nuke-Python-Stubs/nuke_stubs`.

There are a few ways to add them:

- Add the path to the global settings `python.analysis.extraPath`. Keep in mind that, if you need a custom settings in your workspace, the workspace settings will override the global one so you need to re add the stubs path to your workspace settings.
- Add the path to the global setting: `python.analysis.stubPath`. Because this setting is a simple string, only one path can be specified at the time, so if you are using it for something else, you need to move the stubs folder into that location.

## 1.4. BlinkScript

> NOTE: BlinkScript features are available in a basic form. If you would like to see something more, feel free to make a request or open a PR. Also check out [Material Icon Theme](https://marketplace.visualstudio.com/items?itemName=PKief.material-icon-theme) that adds a Nuke icon for the .blink file.

### 1.4.1. Features

- Code execution.
- Syntax highlighting.
- Code formatting.
- Simple code suggestion.
- Startup saturation snippet.

### 1.4.2. Execute BlinkScript

You can execute code from Visual Studio Code directly inside a Nuke BlinkScript node.

The extension will take the name of the current active file and create a blinkscript node inside Nuke with the name as the current filename. If the node already exists then will only modified its source code. Once done will recompile the kernel.

The accepted file extension to execute BlinkScript code are `.cpp` or `.blink`.

## 1.5. Available Commands

All commands are available by opening the Command Palette (`Command+Shift+P` on macOS and `Ctrl+Shift+P` on Windows/Linux) and typing in one of the following Command Name:

| Command Name                               | Command ID                        | Description                                     |
| ------------------------------------------ | --------------------------------- | ----------------------------------------------- |
| `Nuke: Launch main executable`             | `nuke-tools.launchNuke`           | Launch main executable                          |
| `Nuke: Launch alternative executable`      | `nuke-tools.launchNukeAlt`        | Launch alternative executable                   |
| `Nuke: Launch main executable with prompt` | `nuke-tools.launchNukeOptArgs`    | Launch main exec. with prompt for optional args |
| `Nuke: Run Inside Nuke`                    | `nuke-tools.runCodeInsideNuke`    | Execute code inside nuke                        |
| `Nuke: Show Network Addresses`             | `nuke-tools.showNetworkAddresses` | Show network addresses                          |
| `Nuke: Add Stubs to Workspace`             | `nuke-tools.addPythonStubs`       | Add stubs path to workspace settings            |
| `Nuke: Debug Message`                      | `nuke-tools.testRunInsideNuke`    | Quick test connection                           |

By default the extension does not provide any shortcut, but every command can be assigned to one. (see [Key Bindings for Visual Studio Code](https://code.visualstudio.com/docs/getstarted/keybindings) for more information)

Example `json`

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

`Nuke: Run Code Inside Nuke` can be access also via a button in the Editor Toolbar.

## 1.6. Extension Settings

### 1.6.1. `nukeTools.nukeExecutable.primaryExecutablePath`

Primary path for the Nuke executable.

- On MacOS you can find the file with: _Show Package Contents -> Contents/MacOS/Nuke..._
- On Windows WSL the path should be the Unix style: _/mnt/c/Program Files/..._

### 1.6.2. `nukeTools.nukeExecutable.secondaryExecutablePath`

Same as primary executable. Could be a different Nuke version.

### 1.6.3. `nukeTools.nukeExecutable.options.defaultCommandLineArguments`

Command line arguments to be added at each "Nuke launch" 🚀.

### 1.6.4. `nukeTools.nukeExecutable.options.restartInstance`

Restart the terminal instance instead of creating new ones. **Use with caution** as this option will terminate every Nuke process created by the extension. Useful when rapid testing GUI plugins and don't need to save the Nuke comp.

### 1.6.5. `nukeTools.other.clearPreviousOutput`

Clear previous console output before next code execution.

### 1.6.6. `nukeTools.network.enableManualConnection`

If enabled, `nukeTools.network.port` and `nukeTools.network.host` will take over the default settings. Needed when connecting to another computer.

### 1.6.7. `nukeTools.network.port`

Specify a different port for the connection. This will only work if `nukeTools.network.enableManualConnection` is enabled. Server address should be taken from the Nuke plugin.

### 1.6.8. `nukeTools.network.host`

Same as `nukeTools.network.port`. Host could be the localhost or the local ip.

### 1.6.9. `nukeTools.network.debug`

Show network debug information in the output window. Enabling this option, will prevent the console from being cleared after code execution.


## 1.7. Overview

Code execution.

<img title="CommentUncommentDelete" src="https://raw.githubusercontent.com/sisoe24/Nuke-Tools/main/images/execute_code.gif" width="80%"/>

Python stubs auto-complete

<img title="CommentUncommentDelete" src="https://raw.githubusercontent.com/sisoe24/Nuke-Python-Stubs/main/images/auto_complete.gif" width="80%"/>
