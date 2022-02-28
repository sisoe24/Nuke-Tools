import * as vscode from "vscode";
import * as utils from "./utils";

/**
 * Get the stubs path included with the extension.
 *
 * @returns the stubs path
 */
export function getStubsPath(): string {
    return utils.getIncludedPath("nuke_stubs");
}

/**
 * Check if Python extension is installed.
 *
 * Python could be not installed, in that case adding the stubs to `analysis.extraPaths`
 * will fail.
 *
 * @returns true if extension is installed, false otherwise.
 */
export function isPythonInstalled(): boolean {
    return Boolean(vscode.extensions.getExtension("ms-python.python"));
}

/**
 * Extract a version number from a string.
 *
 * The version will be inside the path name for the extension (eg: virgilsisoe.nuke-tools-0.3.0)
 *
 * @param path - path like string of the stubs path inside package path.
 * @returns the matched version as a `string` or `null` if no version is found.
 */
export function extractVersion(path: string): string | null {
    const pattern = /nuke-tools-([^/]+)/;
    const match = pattern.exec(path);
    if (match) {
        return match[1];
    }
    return null;
}

/**
 * Add stubs path to `python.analysis.extraPaths`.
 *
 * Update configuration value only if value is not present or the version is lower
 * than the current version.
 *
 * Note: The update is made by reference.
 *
 * @param extraPaths - The `python.analysis.extraPaths` array object.
 * @param stubsPath - the stubs path to add in the `extraPaths` configuration.
 * @returns - true if path was added, false otherwise
 */
export function addPath(extraPaths: string[], stubsPath: string): boolean {
    let pathAdded = false;

    for (const path of extraPaths) {
        const versionMatch = extractVersion(path);
        const stubsVersion = extractVersion(stubsPath);

        if (versionMatch && stubsVersion) {
            // extract version from current stubs path is mostly needed for testing.
            if (versionMatch < stubsVersion) {
                const index = extraPaths.indexOf(path);
                extraPaths[index] = stubsPath;
            }
            pathAdded = true;
        }
    }
    return pathAdded;
}

/**
 * Update `python.analysis.extraPath`.
 *
 * If path was already added, will do nothing
 *
 * @param extraPaths - The `python.analysis.extraPaths` array object.
 * @param stubsPath - the stubs path to add in the `extraPaths` configuration.
 */
export function updateAnalysisPath(extraPaths: string[], stubsPath: string): void {
    // if path was already added, do nothing and exit
    if (extraPaths.includes(stubsPath)) {
        return;
    }

    if (!addPath(extraPaths, stubsPath)) {
        extraPaths.push(stubsPath);
    }
}

/**
 * Correct extraPath analysis entry.
 *
 * When updating the extension, workspace `python.analysis.extraPath` would point
 * to the old path, thus breaking the stubs path. This functions aims to update the
 * path each time vscode would reload.
 *
 * TODO: testing
 */
export function correctAnalysisPath(): void {
    const config = vscode.workspace.getConfiguration("python.analysis");
    const extraPaths = config.get("extraPaths") as Array<string>;

    for (let index = 0; index < extraPaths.length; index++) {
        if (RegExp("(virgilsisoe\\.)?nuke-tools").exec(extraPaths[index])) {
            extraPaths.splice(index, 1, getStubsPath());
            config.update("extraPaths", extraPaths);
            break;
        }
    }
}

/**
 * Add stubs folder path to workspace settings `python.analysis.extraPaths`.
 * If path is already present, do nothing.
 */
export function addStubsPath(): boolean {
    if (!isPythonInstalled()) {
        vscode.window.showErrorMessage(
            "Python extension is not installed. Could not add stubs path."
        );
        return false;
    }

    const config = vscode.workspace.getConfiguration("python.analysis");
    const extraPaths = config.get("extraPaths") as Array<string>;

    updateAnalysisPath(extraPaths, getStubsPath());
    config.update("extraPaths", extraPaths);
    return true;
}
