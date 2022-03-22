# Change Log

All notable changes to the "nuke-tools" extension will be documented in this file.

## [0.6.0] 03/22/2022

### Added

- New settings to enable/disable the button in the toolbar.

## [0.5.0] 02/27/2022

### Added

- New command that adds NukeServerSocket plugin inside Nuke's directory (`.nuke`) & `menu.py`.

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

- Fixed file name reference that didn't allow vscode to pick NukeServerSocket port settings automatically.

## [0.0.2] - [0.0.8]

- Minor internal maintenance.

## [0.0.1]

- Initial release.
