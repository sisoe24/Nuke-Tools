import * as vscode from "vscode";
import * as utils from "./utils";

/**
 * Get the stubs path included with the extension.
 *
 * @returns the stubs path
 */
export function getStubsPath(): string {
    return utils.getAssetsPath("nuke-python-stubs");
}

/**
 * Check whether the Python extension is installed, as attempting to add the stubs to analysis.extraPaths will
 * fail if Python is not installed.
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
 * Add the stubs path to python.analysis.extraPaths.
 * Only update the configuration value if the value is not already present or the version is
 * lower than the current version.
 *
 * Note that the update is made by reference value
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
 * If the path has already been added, this function will not modify it
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
 * Determine the configuration for extraPaths based on the current Python server.
 *
 *  - Pylance:  `python.analysis`
 *  - Jedi:  `python.autoComplete`
 *
 * @returns the settings name for the extra paths
 */
export function getAutoCompleteSetting(): string {
    const pythonServer = vscode.workspace.getConfiguration("python").get("languageServer");

    // when pythonServer is Default, we assume that Pylance is installed. But it also be Jedi if Pylance is not installed.
    if (pythonServer === "Jedi") {
        return "python.autoComplete";
    }

    return "python.analysis";
}

/**
 * Correct extraPath analysis entry.
 *
 * When the extension is updated, the python.analysis.extraPath setting in the workspace points to
 * the old path, which can break the path to the stubs.
 * This function is designed to update the path every time VS Code reloads to ensure that the path to the stubs is correct
 *
 * TODO: add testing
 */
export function correctAnalysisPath(): void {
    const config = vscode.workspace.getConfiguration(getAutoCompleteSetting());
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
export async function addStubsPath(): Promise<boolean> {
    if (!isPythonInstalled()) {
        vscode.window.showErrorMessage(
            "Python extension is not installed. Could not add stubs path."
        );
        return false;
    }

    vscode.window.showInformationMessage(`
    Python stubs added. You might need to reload the window for the stubs to work. 
    If you feel that stubs are still not working correctly, you need to update the
    "python.analysis.packageIndexDepths" setting—more on the extension [README](https://github.com/sisoe24/Nuke-Tools#131-stubs-not-working-correctly).`);

    const config = vscode.workspace.getConfiguration(getAutoCompleteSetting());
    const extraPaths = config.get("extraPaths") as Array<string>;

    updateAnalysisPath(extraPaths, getStubsPath());
    config.update("extraPaths", extraPaths);
    return true;
}

/**
 * Refresh the python.analysis path every time VS Code reloads,
 * since the path includes the extension version and newer updates can break the path to the stubs.
 *
 * @param context vscode.ExtensionContext
 */
export function fixAnalysisPath(): void {
    if (isPythonInstalled()) {
        correctAnalysisPath();
    }
}
