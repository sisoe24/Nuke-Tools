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

VS Code extension for running Nuke/Houdini Python code directly from your editor.

- [1. Nuke Tools README](#1-nuke-tools-readme)
  - [1.1. Features](#11-features)
  - [1.2. Requirements](#12-requirements)
  - [1.3. Execute code](#13-execute-code)
  - [1.4. Houdini support](#14-houdini-support)
  - [1.5. Python stubs](#15-python-stubs)
    - [1.5.1. Stubs are not working?](#151-stubs-are-not-working)
  - [1.6. BlinkScript](#16-blinkscript)
  - [1.7. Available Commands](#17-available-commands)
  - [1.8. Environment Variables](#18-environment-variables)
    - [1.8.1. Placeholders and Variables](#181-placeholders-and-variables)
  - [1.9. Additional Settings](#19-additional-settings)
    - [1.9.1. Network Settings](#191-network-settings)
  - [1.10. Windows Users](#110-windows-users)
  - [1.11. Included packages](#111-included-packages)
  - [1.12. Nodes Panel](#112-nodes-panel)
    - [1.12.1. Usage](#1121-usage)
    - [1.12.2. Known Issues and Limitations](#1122-known-issues-and-limitations)
  - [1.13. Contributing](#113-contributing)

## 1.1. Features

- NEW: Houdini Python support.
- Execute code and view output in Visual Studio Code. Simply connect `nukeserversocket` - no config needed on the same machine.
- Nuke/Hiero Python stubs for auto-complete suggestions.
- BlinkScript support.
- PySide2 plugin template.
- Commands for launching executables with optional arguments and environment variables.
- And more...

## 1.2. Requirements

Some commands require `nukeserversocket` to be installed and running.

## 1.3. Execute code

1. Download and install the companion plugin `nukeserversocket` via the command: `Nuke: Add Packages` -> `Nuke Server Socket`.
2. Connect `nukeserversocket` inside Nuke/Houdini.
3. With an active Python/BlinkScript file, use the command `Nuke: Run Inside Nuke` from the Command Palette or use the dedicated button in the editor's top right corner (see Key Bindings for Visual Studio Code for more information).

![CodeExecution](/resources/demo/execute_code.gif)

## 1.4. Houdini support

`nukeserversocket >= 1.2.0` works with Houdini! Note that, while we still uses Nuke-style installation paths and naming conventions, Nuke itself isn't required. Check [nukeserversocket#houdini-installation](https://github.com/sisoe24/nukeserversocket/tree/main?tab=readme-ov-file#122-houdini-installation) for setup instructions.

## 1.5. Python stubs

1. Use the command `Nuke: Add Packages` -> `Python Stubs` to add the stubs to your user `python.analysis.extraPaths` setting. The stubs will be located in the `~/.nuke/NukeTools/stubs` directory.
2. Write `import nuke` into your script and you should see the auto-complete suggestions.

![PythonStubs](/resources/demo/auto_complete.gif)

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

## 1.6. BlinkScript

BlinkScript's features include code execution, syntax highlighting, and suggestions. Use Material Icon extension for icons.

Create/update BlinkScript nodes by running code with `.cpp` or `.blink` extensions via `Nuke: Run code inside nuke`. When running the code, a node with the same name as the file will be created in the current DAG. If the node already exists, the code will be updated and recompiled.

## 1.7. Available Commands

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

## 1.8. Environment Variables

Add environment variables to the terminal instance using the `nukeTools.environmentVariables` setting. The extension assumes that if the key has multiple values, it is to be considered a path and it joins them using the appropriate separator for the detected shell and operating system. Additionally, you can choose to prepend or append the original key as needed.

```json
{
  "nukeTools.environmentVariables": {
    "PATH": ["path1", "path2", "$PATH"]
  }
}
```

>[!TIP]
> These variables apply to all executables. To apply them to specific ones, use the executablesMap option.

### 1.8.1. Placeholders and Variables

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

## 1.9. Additional Settings

You can specify multiple executables for the extension by defining their names, paths (bin), command-line arguments (args), and environment variables (env).

```json
{
  "nukeTools.executablesMap": {
    "NukeX": {
        "bin": "/usr/local/Nuke15.0v4/Nuke15.0",
        "args": "--nukex",
        "env": {
            "NUKE_PATH": [
                "/my/nodes",
                "$NUKE_PATH"
            ]
        }
    },
    "Maya20": {
        "bin": "/usr/autodesk/maya2020/bin/maya",
        "args": ""
    },
    "Houdini": {
        "bin": "/opt/hfs19.5/bin/houdini",
        "args": "",
        "env": {
            "PYTHONPATH": [
                "/my/scripts",
                "$PYTHONPATH"
            ],
            "HOUDINI_PATH": [
                "&",
                "/my/houdini/assets"
            ]
        }
    }
  }
}
```

Use `Nuke: Show Executables` to choose an executable from a quick pick menu. You can also assign keybindings with `nuke-tools.<executableName>`.

```json
{
    "key": "alt+shift+m",
    "command": "nuke-tools.Maya20",
}
```

### 1.9.1. Network Settings

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

From NukeTools 0.15.0, the extension supports environment variables in PowerShell and Command Prompt, auto-detects the shell, and handles Windows-style paths. If you encounter any issues, please open an issue on the GitHub repository.

## 1.11. Included packages

The extension includes the following packages:

- [nukeserversocket](https://github.com/sisoe24/nukeserversocket) - A Python plugin for Nuke that allows you to execute code from an external source.
- [nuke-python-stubs](https://github.com/sisoe24/nuke-python-stubs) - Python stubs for Nuke and Hiero.
- [pyside2-template](https://github.com/sisoe24/pyside2-template#readme) - A PySide2 template project for Nuke.
- [vimdcc](https://github.com/sisoe24/vimdcc) - A Vim-like experience for Nuke's default Script Editor.

> The extension auto-downloads and installs the latest package versions from GitHub, updating monthly. Use `Nuke Extras` -> `Clear Packages Cache` for version issues.
## 1.12. Nodes Panel

> The nodes panel is currently in Preview and may not work as expected. If you encounter any issues, please open an issue on the GitHub repository. You can also request new features or contribute by opening a PR.

![NodesPanel](/resources/demo/nodes_panel.gif)

The nodes panel allows you to view and interact with nodes in the current DAG in Nuke. Currently, the panel only supports adding and editing Python Knobs, including the `knobChanged` knob.

### 1.12.1. Usage

Click Nuke icon in Activity Bar for nodes panel. Connect to nukeserversocket to see DAG nodes. Add knobs with `+` button. Edit file references and sync with "Send code to Knob". For `knobChanged`, enter name when creating knob. Click "Refresh" for new knobs, "Sync Nodes" for renamed nodes.

### 1.12.2. Known Issues and Limitations

- Knob scripts are tied to the current Workspace (`$workspace/.nuketools`). If you change the Workspace, the panel will not be able to find the knob files.
- Use alphanumeric characters and underscores for knob names.
- After syncing the knob's value, Nuke may not execute the code until you execute a command in the Script Editor. This is a Nuke-specific issue and not related to the extension. I am still trying to understand why this happens so if you have any ideas, let me know.

## 1.13. Contributing

Contributions are welcome! If you have any ideas or suggestions, please open an issue or a pull request. At the moment, the extension tests are broken. I will try to fix them as soon as possible.
