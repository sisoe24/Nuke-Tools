# 1. Nuke Tools README

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/b4124a14ccb4467b89ec8cd607b0d16f)](https://www.codacy.com/gh/sisoe24/Nuke-Tools/dashboard?utm_source=github.com&utm_medium=referral&utm_content=sisoe24/Nuke-Tools&utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/b4124a14ccb4467b89ec8cd607b0d16f)](https://www.codacy.com/gh/sisoe24/Nuke-Tools/dashboard?utm_source=github.com&utm_medium=referral&utm_content=sisoe24/Nuke-Tools&utm_campaign=Badge_Coverage)
[![DeepSource](https://deepsource.io/gh/sisoe24/Nuke-Tools.svg/?label=active+issues&show_trend=true&token=HEB3mg6EWSs71ckagYV0_P2u)](https://deepsource.io/gh/sisoe24/Nuke-Tools/?ref=repository-badge)

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

[![Main Build](https://img.shields.io/github/v/release/sisoe24/NukeServerSocket?label=NukeServerSocket)](https://github.com/sisoe24/NukeServerSocket/releases)
[![Main Build](https://img.shields.io/github/v/release/sisoe24/nuke-python-stubs?label=nuke-python-stubs)](https://github.com/sisoe24/nuke-python-stubs/releases)
[![Main Build](https://img.shields.io/github/v/release/sisoe24/pyside2-template?label=pyside2-template)](https://github.com/sisoe24/pyside2-template/releases)
[![Main Build](https://img.shields.io/github/v/release/sisoe24/vimdcc?label=vimdcc)](https://github.com/sisoe24/vimdcc/releases)

---

Seamlessly integrate Nuke into your Visual Studio Code workflow, enabling you to write, execute, and debug Nuke scripts with ease.

- [1. Nuke Tools README](#1-nuke-tools-readme)
  - [1.1. Features](#11-features)
  - [1.2. Requirements](#12-requirements)
  - [1.3. Execute code](#13-execute-code)
  - [1.4. Included packages](#14-included-packages)
    - [1.4.1. Python stubs](#141-python-stubs)
      - [1.4.1.1. Stubs are not working?](#1411-stubs-are-not-working)
    - [1.4.2. PySide2 Template Project](#142-pyside2-template-project)
    - [1.4.3. VimDcc](#143-vimdcc)
  - [1.5. Nodes Panel](#15-nodes-panel)
    - [1.5.1. Usage](#151-usage)
    - [1.5.2. Known Issues and Limitations](#152-known-issues-and-limitations)
  - [1.6. BlinkScript](#16-blinkscript)
  - [1.7. Available Commands](#17-available-commands)
  - [1.8. Extension Settings](#18-extension-settings)
  - [1.9. Known Issues](#19-known-issues)
  - [1.10. Contributing](#110-contributing)

## 1.1. Features

- Execute code and view the Nuke execution output in Visual Studio Code
- No configuration is required when using the extension on the same machine. Simply run NukeServerSocket within Nuke.
- Provides BlinkScript support.
- Provides Nuke/Hiero Python stubs for auto-complete suggestions.
- Adds syntax highlighting for .nk and .gizmo files.
- Includes a PySide2 plugin template.
- Provides commands for launching Nuke instances with default or optional arguments via the terminal.
- Enables adding environment variables to running Nuke instances.
- A node panel that allows you to view and interact with the nodes from Nuke current DAG.

## 1.2. Requirements

The interaction with Nuke is only possible when NukeServerSocket is up and running.

## 1.3. Execute code

1. Download and install the companion plugin NukeServerSocket:
    - Via the Command Palette: `Nuke: Add NukeServerSocket` (more info on [Available Commands](#17-available-commands)).
    - [Github](https://github.com/sisoe24/NukeServerSocket/releases)
    - [Nukepedia](http://www.nukepedia.com/python/misc/nukeserversocket)
2. Connect NukeServerSocket inside Nuke.
3. With an active Python/BlinkScript file, use the command `Nuke: Run Inside Nuke` from the Command Palette or use the dedicated button in the editor's top right corner.

![CodeExecution](/resources/images/execute_code.gif)

## 1.4. Included packages

### 1.4.1. Python stubs

> UPDATE: From NukeTools 0.12.0, the stubs are now added inside `~/.nuke/NukeTools/stubs` and are added to the user settings instead of workspace.

1. Use the command `Nuke: Add Python Stubs` to add the stubs to your user `python.analysis.extraPaths` setting.
2. Write `import nuke` into your script.

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

### 1.4.2. PySide2 Template Project

Quickly create a PySide2 template project with the `Nuke: Create a PySide2` command. The plugin can be found in `~/.nuke/NukeTools` . For more information, refer to the project's GitHub README [https://github.com/sisoe24/pyside2-template#readme].

### 1.4.3. VimDcc

VimDcc offers a Vim-like experience for Nuke's default Script Editor. It's perfect for quick coding without an IDE. Check out the project's GitHub README [vimdcc](github.com/sisoe24/vimdcc) for more info. To install, use `Nuke: Install VimDcc`.

## 1.5. Nodes Panel

> The nodes panel is currently in Preview and may not work as expected. If you encounter any issues, please open an issue on the GitHub repository. You can also request new features or contribute by opening a PR.

![NodesPanel](/resources/images/nodes_panel.gif)

The nodes panel allows you to view and interact with nodes in the current DAG in Nuke. Currently, the panel only supports adding and editing Python Knobs, including the `knobChanged` knob.

### 1.5.1. Usage

Access the nodes panel by clicking on the Nuke icon in the Activity Bar. The panel will be empty until you connect [NukeServerSocket](https://github.com/sisoe24/NukeServerSocket) and make sure that the Code Execution Engine is set to `Script Editor`. Once connected, the panel will be populated with nodes from the current DAG.
After adding a new knob in Nuke, you'll need to refresh with the "Refresh" button to see the new knob.

Click the `+` button on a node in the panel to assign it a new knob. Each knob has a file reference which you can edit. Once you save the file, you can sync the file content with the knob by clicking the "Send code to Knob" button. To use the `knobChanged`, type its name into the input dialog when creatin a new knob.

If you change a node's name in Nuke, you'll need to sync it with the panel by clicking the Sync Nodes button which can be found in the panel's top right corner.

### 1.5.2. Known Issues and Limitations

- The panel only works with NukeServerSocket Scritp Editor engine (see [Known Issues](#19-known-issues)).
- Knob scripts are tied to the current Workspace, which means that once you create a knob file, it will be saved in the current `$workspace/.nuketools` directory. If you change the Workspace, the panel will not be able to find the knob files.
- After syncing the knob's value, Nuke may not execute the code until you execute a command in the Script Editor. This is a Nuke-specific issue and not related to the extension. I am still trying to understand why this happens so if you have any ideas, let me know.
- When creatin a new knob, the input prompt for the name is not restrictive as the one in Nuke. This means that you can enter any character, including invalid ones, and the panel will not be able to detect it. Please keep this in mind and use only letters, numbers, and underscores.

## 1.6. BlinkScript

BlinkScript features are currently basic, but you can request more or contribute by opening a PR. Also, try using Material Icon Theme which adds a Nuke icon for the .blink file.

Features include code execution, syntax highlighting, formatting, simple code suggestion, and a startup saturation snippet. When using the extension, a blinkscript node will be created with the same name as the active file, and if the node already exists, the code will be updated and recompiled. Accepted file extensions are `.cpp` or `.blink` .

To create a new BlinkScript node, make sure that the NukeServerSocket Code execution engine is set to the `Script Editor` (see [Known Issues](#19-known-issues)). Once done, create a new file with the `.cpp` or `.blink` extension, and run the code with the command `Nuke: Run code inside nuke`. The node will be created in the current DAG. If you want to update the code, simply run the code again.

## 1.7. Available Commands

- All commands are available by opening the Command Palette (`Command+Shift+P` on macOS and `Ctrl+Shift+P` on Windows/Linux) and typing in one of the following Command Name:

| Command Name                                      | Command ID                        | Description                                                                     |
| ------------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------- |
| `Nuke: Launch main executable`                    | `nuke-tools.launchNuke`           | Launch main executable                                                          |
| `Nuke: Launch alternative executable`             | `nuke-tools.launchNukeAlt`        | Launch alternative executable                                                   |
| `Nuke: Launch alternative executable with prompt` | `nuke-tools.launchNukeOptArgs`    | Launch alternative exec. with prompt for optional args                          |
| `Nuke: Run Inside Nuke`                           | `nuke-tools.runCodeInsideNuke`    | Execute code inside Nuke                                                        |
| `Nuke: Add Python Stubs`                    | `nuke-tools.addPythonStubs`       | Add stubs path to workspace settings                                            |
| `Nuke: Add NukeServerSocket`                      | `nuke-tools.addNukeServerSocket`  | Add NukeServerSocket plugin to `.nuke` dir and `menu.py`                        |
| `Nuke: Add VimDcc`                      | `nuke-tools.addVimDcc`  | Add VimDcc plugin to `.nuke` dir and `menu.py`                        |
| `Nuke: Create a PySide2 plugin`                   | `nuke-tools.createPySide2Project` | Create a PySide2 plugin from template                                           |
| `Nuke: Show Network Addresses`                    | `nuke-tools.showNetworkAddresses` | Show network addresses                                                          |
| `Nuke: Force Update packages`                     | `nuke-tools.forceUpdatePackages`  | Update the included packages (NukeServerSocket, Python stubs, pyside2-template) |

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
    Restart the terminal instance instead of creating new ones. **Use with caution**. This option will terminate every Nuke process spawned by the extension. Useful when rapid testing GUI plugins that don't need saving the composition.

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

    Add environment variables the current running Nuke instance. At the moment, it does not take in account the system environment variables.

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

- `nukeTools.pysideTemplate.pythonVersion`: `string`
    Set a default Python version to use in pyproject.toml. You can use
    Poetry [version-constraints](https://python-poetry.org/docs/dependency-specification/#version-constraints) specification (e.g. `~3.7.7`)

- `nukeTools.pysideTemplate.pysideVersion`: `string`
    Set a default PySide2 version to use in pyproject.toml and requirements.txt. (e.g. `5.12.2`)

## 1.9. Known Issues

- There is a bug in NukeServerSocket <= 0.6.1 that wrongly assumes the server is set on using the Script Editor engine. The NodesPanel and the BlinkScript features do not work with the Nuke Internal engine, so you'll need to switch to the Internal Engine and then back to the ScriptEditor engine. This will force NukeServerSocket to use the Script Editor engine. This issue is fixed in 0.6.2.

## 1.10. Contributing

Contributions are welcome! If you have any ideas or suggestions, please open an issue or a pull request. At the moment, the extension tests are broken. I will try to fix them as soon as possible.
