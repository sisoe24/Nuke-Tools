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
  - [1.4. nukeserversocket](#14-nukeserversocket)
  - [1.5. Python stubs](#15-python-stubs)
    - [1.5.1. Stubs are not working?](#151-stubs-are-not-working)
  - [1.6. Nodes Panel](#16-nodes-panel)
    - [1.6.1. Usage](#161-usage)
    - [1.6.2. Known Issues and Limitations](#162-known-issues-and-limitations)
  - [1.7. BlinkScript](#17-blinkscript)
  - [1.8. Available Commands](#18-available-commands)
  - [1.9. Environment Variables](#19-environment-variables)
    - [Placeholders and Variables](#placeholders-and-variables)
  - [1.9.1. Additional Settings](#191-additional-settings)
    - [1.9.2. Network Settings](#192-network-settings)
  - [1.10. Windows Users](#110-windows-users)
  - [1.11. Included packages](#111-included-packages)
  - [1.12. Known Issues](#112-known-issues)
  - [1.13. Contributing](#113-contributing)

## 1.1. Features

- Execute code and view Nuke execution output in Visual Studio Code. Just connect `nukeserversocket` inside Nuke - no config needed on the same machine.
- Nuke/Hiero Python stubs for auto-complete suggestions.
- BlinkScript support.
- PySide2 plugin template.
- Commands for launching executables with optional arguments and environment variables.
- And more...

## 1.2. Requirements

Some commands require `nukeserversocket` to be installed and running in Nuke.

## 1.3. Execute code

1. Download and install the companion plugin `nukeserversocket` via the command: `Nuke: Add Packages` -> `nukeServerSocket`.
2. Connect `nukeserversocket` inside Nuke.
3. With an active Python/BlinkScript file, use the command `Nuke: Run Inside Nuke` from the Command Palette or use the dedicated button in the editor's top right corner (see Key Bindings for Visual Studio Code for more information).

![CodeExecution](/resources/images/execute_code.gif)

## 1.4. nukeserversocket

NukeServerSocket has been updated to version 1.0.0. There are some breaking changes, such as dropping support for Python 2.7 and changing the configuration file. The extension still supports the old configuration file (NukeServerSocket.ini), in case you still need to use any version <= 0.6.2 but its up to you to download and install it since the extension will only download the latest version. Also the package name has been changed from `NukeServerSocket` to `nukeserversocket`.

If you encounter any issues, please open an issue on the GitHub repository.

## 1.5. Python stubs

1. Use the command `Nuke: Add Packages` -> `pythonStubs` to add the stubs to your user `python.analysis.extraPaths` setting. The stubs will be located in the `~/.nuke/NukeTools/stubs` directory.
2. Write `import nuke` into your script and you should see the auto-complete suggestions.

![PythonStubs](/resources/images/auto_complete.gif)

### 1.5.1. Stubs are not working?

If you're experiencing issues with the stubs in the latest versions of VSCode, you may find it helpful to adjust the `python.analysis.packageIndexDepths` setting.

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

## 1.6. Nodes Panel

> The nodes panel is currently in Preview and may not work as expected. If you encounter any issues, please open an issue on the GitHub repository. You can also request new features or contribute by opening a PR.

![NodesPanel](/resources/images/nodes_panel.gif)

The nodes panel allows you to view and interact with nodes in the current DAG in Nuke. Currently, the panel only supports adding and editing Python Knobs, including the `knobChanged` knob.

### 1.6.1. Usage

Click Nuke icon in Activity Bar for nodes panel. Connect to nukeserversocket to see DAG nodes. Add knobs with `+` button. Edit file references and sync with "Send code to Knob". For `knobChanged`, enter name when creating knob. Click "Refresh" for new knobs, "Sync Nodes" for renamed nodes.

### 1.6.2. Known Issues and Limitations

- The panel only works with nukeserversocket Scritp Editor engine (see [Known Issues](#19-known-issues)).
- Knob scripts are tied to the current Workspace (`$workspace/.nuketools`). If you change the Workspace, the panel will not be able to find the knob files.
- Use alphanumeric characters and underscores for knob names.
- After syncing the knob's value, Nuke may not execute the code until you execute a command in the Script Editor. This is a Nuke-specific issue and not related to the extension. I am still trying to understand why this happens so if you have any ideas, let me know.

## 1.7. BlinkScript

BlinkScript's features include code execution, syntax highlighting, and suggestions. Use Material Icon extension for icons.

Create/update BlinkScript nodes by running code with `.cpp` or `.blink` extensions via `Nuke: Run code inside nuke`. When running the code, a node with the same name as the file will be created in the current DAG. If the node already exists, the code will be updated and recompiled.

> Ensure nukeserversocket is set to `Script Editor`. See [Known Issues](#19-known-issues) for setup.

## 1.8. Available Commands

- All commands are available by opening the Command Palette (`Command+Shift+P` on macOS and `Ctrl+Shift+P` on Windows/Linux) and typing in one of the following Command Name:

| Command Name                          | Command ID                     | Description                                     |
| ------------------------------------- | ------------------------------ | ----------------------------------------------- |
| `Nuke: Run Inside Nuke`               | `nuke-tools.runCodeInsideNuke` | Execute code inside Nuke                        |
| `Nuke: Launch main executable`        | `nuke-tools.launchNuke`        | Launch main executable                          |
| `Nuke: Launch executable with prompt` | `nuke-tools.launchNukeOptArgs` | Launch executable with prompt for optional args |
| `Nuke: Add Packages`                  | `nuke-tools.addPackages`       | Add packages to `.nuke/NukeTools` dir           |
| `Nuke: Extras`                        | `nuke-tools.extras`            | Show extra commands                             |
| `Nuke: Show Executables`              | `nuke-tools.showExecutables`   | Show available executables                      |
| `Nuke: Open Nuke Script`              | `nuke-tools.openNukeScript`    | Open the current script in Nuke                 |

NOTES:

- Running `Nuke: Add Package` will add the corresponding plugin to `$HOME/.nuke/NukeTools` and generate an import statement in the menu.py file. If menu.py doesn't exist, it will be created.
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

## 1.9. Environment Variables

Add environment variables to the terminal instance using the `nukeTools.environmentVariables` setting.

```json
{
  "nukeTools.environmentVariables": {
    "VAR_NAME": ["value1", "value2", ...]
  }
}
```

### Placeholders and Variables

- `${workspaceFolder}`: Current workspace folder
- `${workspaceFolderBasename}`: Name of the workspace folder
- `${userHome}`: User's home directory
- `$VAR_NAME`: System environment variables

Example

```json
{
  "nukeTools.environmentVariables": {
    "NUKE_PATH": [
      "${workspaceFolder}/gizmo",
      "$NUKE_PATH"
    ],
    "PYTHONPATH": [
      "$MYLIB/path/to/python/lib"
    ],
    "API_KEY": [
      "0a9f0381-aebb-4e40-a77a-2c381b08e0ea"
    ]
  }
}
```

The extension combines arrays of strings using the appropriate separator for the detected shell and operating system.

## 1.9.1. Additional Settings

You can define multiple executables for the extension by specifying their names, paths (bin), and command-line arguments (args).

```json
{
  "nukeTools.executablesMap": {
    "NukeX": {
        "bin": "/usr/local/Nuke15.0v4/Nuke15.0",
        "args": "--nukex"
    },
    "Maya20": {
        "bin": "/usr/autodesk/maya2020/bin/maya",
        "args": ""
    }
  }
}
```

Use `Nuke: Show Executables` to choose an executable from a quick pick menu. You can also ASsign keybindings with `nuke-tools.<executableName>`.

```json
{
    "key": "alt+shift+m",
    "command": "nuke-tools.Maya20",
}
```

> Note: You need to restart vscode after adding new executables.

### 1.9.2. Network Settings

If you want to manually connect to a difference NukeServerSocket instance, you can set the `active` key to `true` and add the `host` and `port` keys.

```json
{
    "nukeTools.network.manualConnection": {
        "active": false,
        "host": "localhost",
        "port": "49512"
    }
}
```

## 1.10. Windows Users

From NukeTools 0.15.0, the extension supports environment variables in PowerShell and Command Prompt, auto-detects the shell, and handles Windows-style paths. If you encounter any issues, please open an issue on the GitHub repository..

## 1.11. Included packages

The extension includes the following packages:

- [nukeserversocket](https://github.com/sisoe24/nukeserversocket) - A Python plugin for Nuke that allows you to execute code from an external source.
- [nuke-python-stubs](https://github.com/sisoe24/nuke-python-stubs) - Python stubs for Nuke and Hiero.
- [pyside2-template](https://github.com/sisoe24/pyside2-template#readme) - A PySide2 template project for Nuke.
- [vimdcc](https://github.com/sisoe24/vimdcc) - A Vim-like experience for Nuke's default Script Editor.

> The extension auto-downloads and installs the latest package versions from GitHub, updating monthly. Use `Nuke Extras` -> `Clear Packages Cache` for version issues.

## 1.12. Known Issues

- There is a bug in nukeserversocket <= 0.6.1 that wrongly assumes the server is set on using the Script Editor engine. The NodesPanel and the BlinkScript features do not work with the Nuke Internal engine, so you'll need to switch to the Internal Engine and then back to the ScriptEditor engine. This will force nukeserversocket to use the Script Editor engine. This issue is fixed in 0.6.2 and above.

## 1.13. Contributing

Contributions are welcome! If you have any ideas or suggestions, please open an issue or a pull request. At the moment, the extension tests are broken. I will try to fix them as soon as possible.
