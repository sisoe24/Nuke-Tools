import * as vscode from "vscode";

export function getStubsPath(): string {
    const currentPath = vscode.extensions.getExtension("virgilsisoe.nuke-tools")!.extensionPath;
    return require("path").join(currentPath, "Nuke-Python-Stubs", "nuke_stubs");
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
 * @returns the matched version as a string or undefined if no version is found.
 */
export function extractVersion(path: string): string | undefined {
    const match = path.match(/nuke-tools-([^\/]+)/);
    if (match) {
        return match[1];
    }
    return undefined;
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

        if (versionMatch) {
            // extract version from current stubs path is mostly needed for testing.
            if (versionMatch < extractVersion(stubsPath)!) {
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

    const stubsPath = getStubsPath();

    const config = vscode.workspace.getConfiguration("python.analysis");
    const extraPaths = config.get("extraPaths") as Array<string>;

    updateAnalysisPath(extraPaths, stubsPath);
    config.update("extraPaths", extraPaths);
    return true;
}
