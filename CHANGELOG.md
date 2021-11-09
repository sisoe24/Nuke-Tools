# Change Log

All notable changes to the "nuke-tools" extension will be documented in this file.

## [0.3.2] 11/08/2021

Mostly code refactoring and test suite.

### Changed

- Extension now activates on `onStartupFinished`.

### Fixed

- Adding the stubs will not create a duplicate if extension version is different.

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
