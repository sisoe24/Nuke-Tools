# 1. Nuke Tools README

<!-- [![Codacy Badge](https://app.codacy.com/project/badge/Grade/b4124a14ccb4467b89ec8cd607b0d16f)](https://www.codacy.com/gh/sisoe24/Nuke-Tools/dashboard?utm_source=github.com&utm_medium=referral&utm_content=sisoe24/Nuke-Tools&utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/b4124a14ccb4467b89ec8cd607b0d16f)](https://www.codacy.com/gh/sisoe24/Nuke-Tools/dashboard?utm_source=github.com&utm_medium=referral&utm_content=sisoe24/Nuke-Tools&utm_campaign=Badge_Coverage)
[![DeepSource](https://deepsource.io/gh/sisoe24/Nuke-Tools.svg/?label=active+issues&show_trend=true&token=HEB3mg6EWSs71ckagYV0_P2u)](https://deepsource.io/gh/sisoe24/Nuke-Tools/?ref=repository-badge) -->

[![vscode-marketplace](https://img.shields.io/badge/vscode-marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools)
[![vscode-version](https://img.shields.io/visual-studio-marketplace/v/virgilsisoe.nuke-tools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools&ssr=false#version-history)
[![vscode-installs](https://img.shields.io/visual-studio-marketplace/i/virgilsisoe.nuke-tools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools)
[![vscode-ratings](https://img.shields.io/visual-studio-marketplace/r/virgilsisoe.nuke-tools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools&ssr=false#review-details)
[![vscode-last-update](https://img.shields.io/visual-studio-marketplace/last-updated/virgilsisoe.nuke-tools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools)

[![openvsx-marketplace](https://img.shields.io/badge/openvsx-marketplace-C160EF)](https://open-vsx.org/extension/virgilsisoe/nuke-tools)
[![openvsx-version](https://img.shields.io/open-vsx/v/virgilsisoe/nuke-tools?label=version)](https://open-vsx.org/extension/virgilsisoe/nuke-tools/changes)
[![openvsx-downloads](https://img.shields.io/open-vsx/dt/virgilsisoe/nuke-tools)](https://open-vsx.org/extension/virgilsisoe/nuke-tools)
[![openvsx-rating](https://img.shields.io/open-vsx/rating/virgilsisoe/nuke-tools)](https://open-vsx.org/extension/virgilsisoe/nuke-tools/reviews)

Includes the following packages:

[![nukeserversocket](https://img.shields.io/github/v/release/sisoe24/nukeserversocket?label=nukeserversocket)](https://github.com/sisoe24/nukeserversocket/releases)
[![stubs](https://img.shields.io/github/v/release/sisoe24/nuke-python-stubs?label=nuke-python-stubs)](https://github.com/sisoe24/nuke-python-stubs/releases)
[![pysidetemplate](https://img.shields.io/github/v/release/sisoe24/pyside2-template?label=pyside2-template)](https://github.com/sisoe24/pyside2-template/releases)
[![vimdcc](https://img.shields.io/github/v/release/sisoe24/vimdcc?label=vimdcc)](https://github.com/sisoe24/vimdcc/releases)

---

Seamlessly integrate Nuke into your Visual Studio Code workflow, enabling you to write, execute, and debug Nuke scripts with ease.

- [1. Nuke Tools README](#1-nuke-tools-readme)
  - [1.1. Features](#11-features)
  - [1.2. Requirements](#12-requirements)
  - [1.3. Execute code](#13-execute-code)
  - [1.4. Included packages](#14-included-packages)
    - [1.4.0. nukeserversocket](#140-nukeserversocket)
    - [1.4.1. Python stubs](#141-python-stubs)
      - [1.4.1.1. Stubs are not working?](#1411-stubs-are-not-working)
  - [1.5. Nodes Panel](#15-nodes-panel)
    - [1.5.1. Usage](#151-usage)
    - [1.5.2. Known Issues and Limitations](#152-known-issues-and-limitations)
  - [1.6. BlinkScript](#16-blinkscript)
  - [1.7. Available Commands](#17-available-commands)
  - [1.8. Extension Settings](#18-extension-settings)
  - [1.9. Known Issues](#19-known-issues)
  - [1.10. Contributing](#110-contributing)

## 1.1. Features

- Execute code and view Nuke execution output in Visual Studio Code. Just run `nukeserversocket` within Nuke - no config needed on the same machine.
- BlinkScript support.
- Nuke/Hiero Python stubs for auto-complete suggestions.
- Syntax highlighting for .nk and .gizmo files.
- PySide2 plugin template.
- Commands for launching Nuke with default or optional arguments via the terminal.
- Add environment variables to running Nuke instances.
- A node panel that allows you to view and interact with the nodes from Nuke current DAG.

## 1.2. Requirements

The interaction with Nuke is only possible when `nukeserversocket` is up and running.

## 1.3. Execute code

1. Download and install the companion plugin `nukeserversocket` via the command: `Nuke: Add nukeserversocket`.
2. Connect nukeserversocket inside Nuke.
3. With an active Python/BlinkScript file, use the command `Nuke: Run Inside Nuke` from the Command Palette or use the dedicated button in the editor's top right corner.

![CodeExecution](/resources/images/execute_code.gif)

## 1.4. Included packages

The extension includes the following packages:

- [nukeserversocket](https://github.com/sisoe24/nukeserversocket) - A Python plugin for Nuke that allows you to execute code from an external source.
- [nuke-python-stubs](https://github.com/sisoe24/nuke-python-stubs) - Python stubs for Nuke and Hiero.
- [pyside2-template](https://github.com/sisoe24/pyside2-template#readme) - A PySide2 template project for Nuke.
- [vimdcc](https://github.com/sisoe24/vimdcc) - A Vim-like experience for Nuke's default Script Editor.

> When you add any of these packages, the extension will automatically download the latest version from the GitHub repository, install it and cache it for you. Subsequent updates will also be handled by the extension automatically every month. If you notice and version discrepancies, you can use the command `Nuke: Clear Packages Cache` to clear the cache.

### 1.4.0. nukeserversocket

NukeServerSocket has been updated to version 1.0.0. There are some breaking changes, such as dropping support for Python 2.7 and changing the configuration file. The extension still supports the old configuration file (NukeServerSocket.ini), in case you still need to use any version <= 0.6.2 but its up to you to download and install it since the extension will only download the latest version. Also the package name has been changed from `NukeServerSocket` to `nukeserversocket`.

If you encounter any issues, please open an issue on the GitHub repository. Sorry for the inconvenience.

### 1.4.1. Python stubs

1. Use the command `Nuke: Add Python Stubs` to add the stubs to your user `python.analysis.extraPaths` setting. The stubs will be located in the `~/.nuke/NukeTools/stubs` directory.
2. Write `import nuke` into your script and you should see the auto-complete suggestions.

![PythonStubs](/resources/images/auto_complete.gif)

#### 1.4.1.1. Stubs are not working?

If you're experiencing issues with the stubs in the latest versions of VSCode, you may find it helpful to adjust the `python.analysis.packageIndexDepths` setting. Try setting it to something like this:

```json
"python.analysis.packageIndexDepths": [
     {
         "depth": 5,
         "includeAllSymbols": true,
         "name": "nuke"
     },
     {
         "depth": 5,
         "includeAllSymbols": true,
         "name": "hiero"
     },
]
```

## 1.5. Nodes Panel

> The nodes panel is currently in Preview and may not work as expected. If you encounter any issues, please open an issue on the GitHub repository. You can also request new features or contribute by opening a PR.

![NodesPanel](/resources/images/nodes_panel.gif)

The nodes panel allows you to view and interact with nodes in the current DAG in Nuke. Currently, the panel only supports adding and editing Python Knobs, including the `knobChanged` knob.

### 1.5.1. Usage

To access the nodes panel, click on the Nuke icon in the Activity Bar. Connect to the nukeserversocket and the panel will show nodes from the current DAG.

To assign a new knob to a node, click the `+` button on the node panel. Edit each knob's file reference and sync it with the knob using the "Send code to Knob" button. To use `knobChanged`, type its name into the input dialog when creating a new knob.

If you add a new knob, click "Refresh" to view it. If you change a node's name, click "Sync Nodes" to sync it with the panel.

### 1.5.2. Known Issues and Limitations

- The panel only works with nukeserversocket Scritp Editor engine (see [Known Issues](#19-known-issues)).
- Knob scripts are tied to the current Workspace, which means that once you create a knob file, it will be saved in the current `$workspace/.nuketools` directory. If you change the Workspace, the panel will not be able to find the knob files.
- After syncing the knob's value, Nuke may not execute the code until you execute a command in the Script Editor. This is a Nuke-specific issue and not related to the extension. I am still trying to understand why this happens so if you have any ideas, let me know.
- The knob name input prompt is not as restrictive as in Nuke. Use only letters, numbers, and underscores to avoid issues..

## 1.6. BlinkScript

BlinkScript features are currently basic, but you can request more or contribute by opening a PR. Also, try using Material Icon Theme which adds a Nuke icon for the .blink file.

Features include code execution, syntax highlighting, formatting, simple code suggestion, and a startup saturation snippet. When using the extension, a blinkscript node will be created with the same name as the active file, and if the node already exists, the code will be updated and recompiled. Accepted file extensions are `.cpp` or `.blink` .

To create a new BlinkScript node, make sure that the nukeserversocket Code execution engine is set to the `Script Editor` (see [Known Issues](#19-known-issues)). Once done, create a new file with the `.cpp` or `.blink` extension, and run the code with the command `Nuke: Run code inside nuke`. The node will be created in the current DAG. If you want to update the code, simply run the code again.

## 1.7. Available Commands

- All commands are available by opening the Command Palette (`Command+Shift+P` on macOS and `Ctrl+Shift+P` on Windows/Linux) and typing in one of the following Command Name:

| Command Name                                      | Command ID                        | Description                                              |
| ------------------------------------------------- | --------------------------------- | -------------------------------------------------------- |
| `Nuke: Launch main executable`                    | `nuke-tools.launchNuke`           | Launch main executable                                   |
| `Nuke: Launch alternative executable`             | `nuke-tools.launchNukeAlt`        | Launch alternative executable                            |
| `Nuke: Launch alternative executable with prompt` | `nuke-tools.launchNukeOptArgs`    | Launch alternative exec. with prompt for optional args   |
| `Nuke: Run Inside Nuke`                           | `nuke-tools.runCodeInsideNuke`    | Execute code inside Nuke                                 |
| `Nuke: Add Python Stubs`                          | `nuke-tools.addPythonStubs`       | Add stubs path to workspace settings                     |
| `Nuke: Add NukeServerSocket`                      | `nuke-tools.addNukeServerSocket`  | Add NukeServerSocket plugin to `.nuke` dir and `menu.py` |
| `Nuke: Add VimDcc`                                | `nuke-tools.addVimDcc`            | Add VimDcc plugin to `.nuke` dir and `menu.py`           |
| `Nuke: Create a PySide2 plugin`                   | `nuke-tools.addPysideTemplate`    | Create a PySide2 plugin from template                    |
| `Nuke: Show Network Addresses`                    | `nuke-tools.showNetworkAddresses` | Show network addresses                                   |
| `Nuke: Clear Packages Cache`                       | `nuke-tools.clearPackagesCache`   | Clear the packages cache                                 |

NOTES:

- When Running `Nuke: Add NukeServerSocket` or `Nuke: Create a Pyside2` plugin will add the corresponding plugin to `$HOME/.nuke/NukeTools` and generate an import statement in the menu.py file. If menu.py doesn't exist, it will be created.
- By default, the extension does not provide any shortcut. But you can assign each command to one. (see [Key Bindings for Visual Studio Code](https://code.visualstudio.com/docs/getstarted/keybindings) for more information).
    Example `keybindings.json` :

    ```json
    [
        {
            "key": "alt+shift+n",
            "command": "nuke-tools.launchNuke"
        },
        {
            "key": "alt+shift+r",
            "command": "nuke-tools.runCodeInsideNuke",
            "when": "editorTextFocus"
        }
    ]
    ```

## 1.8. Extension Settings

- `nukeTools.nukeExecutable.primaryExecutablePath`: `string`
    A path for an executable.
  - On macOS, you can find the file in _Show Package Contents -> Contents/MacOS/Nuke..._
  - On Windows WSL, the path should be in Unix style: _/mnt/c/Program Files/..._

- `nukeTools.nukeExecutable.secondaryExecutablePath`: `string`
    Same as primary executable. It could be a different Nuke version.

- `nukeTools.nukeExecutable.options.defaultCommandLineArguments`: `string`
    Command-line arguments you can add at when running the secondary executable.

- `nukeTools.nukeExecutable.options.restartInstance`: `boolean`
    Restart the terminal instance instead of creating new ones. **Use with caution**. This option will terminate every Nuke process spawned by the extension. Useful when rapid testing GUI plugins.

- `nukeTools.other.clearPreviousOutput`: `boolean`
    Clear the previous console output text.

- `nukeTools.network.enableManualConnection`: `boolean`
    If enabled, `nukeTools.network.port` and `nukeTools.network.host` will take over the default settings. You might need this option when connecting to another computer.
  - `nukeTools.network.port`: `string`
        Specify a different port for the connection. This option only works if `nukeTools.network.enableManualConnection` is active. The server address should be the same as in the Nuke plugin.
  - `nukeTools.network.host`: `string`
        Same as the port. The host could be the local host or the local IP.

- `nukeTools.network.debug`: `boolean`
    Show network debug information in the output window. Enabling this option will not clean the console output after code execution.

- `nukeTools.other.envVars`: `{key: string: value: string}`

    **NOTE**: Currently not working on Windows.

    Add environment variables the current running Nuke instance.

    ```json
    {
        "nukeTools.other.envVars": {
            "NUKE_PATH": "/path/nuke/plugins:/path/nuke/ui",
            "API_KEY": "0a9f0381-aebb-4e40-a77a-2c381b08e0ea"
        }
    }
    ```

- `nukeTools.other.useSystemEnvVars`: `boolean`

    Add system environment variables. When enabled, the extension will also add the corresponding system environment variables to the running Nuke instance.

## 1.9. Known Issues

- There is a bug in nukeserversocket <= 0.6.1 that wrongly assumes the server is set on using the Script Editor engine. The NodesPanel and the BlinkScript features do not work with the Nuke Internal engine, so you'll need to switch to the Internal Engine and then back to the ScriptEditor engine. This will force nukeserversocket to use the Script Editor engine. This issue is fixed in 0.6.2 and above.
  - If you are using nukeserversocket >= 1.0.0, you will not have this option. The extension uses the Script Editor engine by default.

## 1.10. Contributing

Contributions are welcome! If you have any ideas or suggestions, please open an issue or a pull request. At the moment, the extension tests are broken. I will try to fix them as soon as possible.
