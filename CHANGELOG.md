# Change Log

## [0.16.0] - 07/07/2024

### Changed

- Changed the `nuketools.environmentVariables` keys to use an array of strings rather than a single string (`{"VAR_NAME": ["value1", "value2", ...]}`)
- Added new placeholders for the `nuketools.environmentVariables` setting: `${workspaceFolderBasename}` and `${userHome}`.
- Added the ability to use any system environment variable in the `nuketools.environmentVariables` setting.

## [0.15.1] - 07/07/2024

### Fixed

- Placeholder replacement (`${workspaceFolder}`) now works correctly in every command.

## [0.15.0] - 06/07/2024

The main goal of this release is to simplify the extension commands and settings, making it easier to use and understand. This caused some breaking changes, but the extension is now more user-friendly.

### Added

Commands:

- `NukeTools: Open Script in Nuke`: A new command that opens the current active Nuke script with the main executable.
- `NukeTools: Show Executables`: A new command that shows the list of executables added to the extension. via the new setting `nukeTools.executablesMap`.
- `NukeTools: Add Packages`: Show the list of packages available to add to the extension.
- `NukeTools: Extras`: Show the list of extra commands available in the extension.

Settings:

- `nukeTools.executablesMap`: A new setting that allows the user to add multiple executables to the extension.

    ```json
    {
        "nuke": {
            "path": "/path/to/nuke",
            "args": "-t",
        },
        "nukex": {
            "path": "/path/to/nuke",
            "args": "--nukex",
        },
        "maya": {
            "path": "/path/to/maya",
            "args": "",
        }
    }
    ```

### Changed

- All the settings namespaces have been updated thus breaking the previous saved ones.
- The packages commands (Stubs, NukeServerSocket, etc.) are now part of the `NukeTools: Add Packages` command.
- Merged other commands into the `NukeTools: Extras` command.
- Network settings (`host`, `port` and `enable manual connection`) were merged into the new settings `nukeTools.network.manualConnection`.

```json
{
    "nukeTools.network.manualConnection": {
        "active": false,
        "host": "localhost",
        "port": "49512"
    }
}
```

### Removed

Commands:

- `NukeTools: Launch Alternative Executable`
- `nukeTools.other.UseSystemEnvVars`: Removed the setting that allows the use of system environment variables. The settings `nukeTools.environmentVariables` now allows the use of the system environment variables directly in the settings.

```json
{
    "nukeTools.environmentVariables": {
        "NUKE_PATH": "${workspaceFolder}/bin:$NUKE_PATH",
    }
}
```

## [0.14.0] - 02/18/2024

### Changed

- Added a monthly check for the latest included packages.
- Changed the command `Nuke: Add Pyside2 Plugin` functionality to reflect the new changes in the included template.

## [0.13.0] - 03/12/2023

### Added

- New command `Nuke: Add VimDcc` that adds the VimDcc plugin to the current Nuke installation.

## [0.12.1] - 11/19/2023

### Changed

- Update nukeserversocket to version to latest
- Update socket debug functionallity.

## [0.12.0] - 09/23/2023

### Added

- New settings `nukeTools.other.useSystemEnvVars` that allows to use the system environment variables together with the ones defined in the extension settings.

### Changed

- The stubs now are added to the `~/.nuke/NukeTools/stubs` folder and the LSP config path is added at a user level instead of workspace level.

## [0.11.0] 02/07/2023

### Added

- Initial support for some completions providers. Currently only works for the `nuke.toNode` function.

### Changed

- Update the handling of the socket connection to resolve as soon as it receives the data.

## [0.10.0] 04/02/2023

### Added

- Nodes Panel: A new panel that allows interaction with the nodes in the current Nuke script.

## [0.9.0] 03/25/2023

### Changed

- Fetch the latests release of the included packages via the GitHub release page.

## [0.8.12] 03/19/2023

### Added

- New and improved nuke stubs files.

### Changed

- Fallback on Pylance Python Server if Default.
- Include stubs inside zip file.
- Default command line argument command now only works for the second executable.

## [0.8.4] 09/01/2023

### Changed

- Changed Python version for the pyside2 plugin to `~3.7.7`

### Fixed

- Fixed placeholder substitution for pyside2 template name with spaces.
- Remove unnecessary socket connection timeout.

## [0.8.2] 11/20/2022

### Fixed

- Update Hiero stubs with proper `__init__.py` file.

## [0.8.1] 11/20/2022

### Added

- Hiero stubs

## [0.8.0] 10/23/2022

### Added

- New command to create a pyside2 plugin from included template.

### Changed

- Can now add multiple values as environmental variables before launching Nuke, instead of only to NUKE_PATH.

## [0.7.2] 09/04/2022

### Added

- Syntax color for `.nk` and `.gizmo` files.

## [0.7.0] 08/02/2022

### Added

- New settings for adding paths to NUKE_PATH.

## [0.6.2] 06/14/2022

### Added

- Support the Jedi Language Server for Python when adding the stubs files.

## [0.6.0] 03/22/2022

### Added

- New settings to enable/disable the button in the toolbar.

## [0.5.0] 02/27/2022

### Added

- New command that adds nukeserversocket plugin inside Nuke's directory (`.nuke`) & `menu.py`.

## [0.4.5] 02/18/2022

### Fixed

- Fixed formatting error in stubs main init file.

## [0.4.4] 02/17/2022

### Fixed

- Correctly import `nukescripts` module when using the stubs path.

## [0.4.3] 02/02/2022

### Fixed

- Stubs path now will automatically update to reflect the extension path when a new version is released.

### Changed

- Some stubs file will now return `[Node]` instead of `list()`.

## [0.4.1] 02/02/2022

### Fixed

- BlinkScript sample script incorrect components.

## [0.4.0] 12/12/2021

### Added

- BlinkScript syntax highlighting, formatting and simple code suggestion.

### Removed

- `Auto add stubs path` setting.

## [0.3.3] 11/08/2021

Mostly code refactoring and test suite.

### Fixed

- Adding the stubs path will not create a duplicate if extension version is different.

### Removed

- Setting `Auto add stubs path` is now deprecated. Path should be added manually when needed with the command `Add Python Stubs`.

## [0.3.0] 10/04/2021

### Added

- Add python stubs folder to root project.
- New command `Add Python Stubs` that adds the stubs to the project settings.json.
- New settings `Auto add stubs path` that adds the stubs to the project settings.json when workspace contains a `*.py` file.

## [0.2.0] 09/15/2021

### Added

- Support for BlinkScript.

## [0.0.14] 09/12/2021

> This version was wrongfully uploaded as 0.1.0

### Added

- Better check for the .ini file in case has wrong/invalid values.

## [0.0.13] 08/16/2021

### Changed

- Remove Nuke Python Snippets from extension pack.

## [0.0.10] - [0.0.12]

- Minor internal maintenance.

## [0.0.9] - 08/15/2021

### Fixed

- Fixed file name reference that didn't allow vscode to pick nukeserversocket port settings automatically.

## [0.0.2] - [0.0.8]

- Minor internal maintenance.

## [0.0.1]

- Initial release.
