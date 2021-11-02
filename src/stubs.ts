import * as vscode from "vscode";

export function getStubsPath(): string {
    const currentPath = vscode.extensions.getExtension(
        "virgilsisoe.nuke-tools"
    )!.extensionPath;
    return require("path").join(currentPath, "Nuke-Python-Stubs", "nuke_stubs");
}

/**
 * Check if Python extension is installed.
 *
 * Python could be not installed, in that case adding the stubs to `analysis.extraPaths`
 * will fail.
 *
 * @returns An extension or undefined
 */
function isPythonInstalled() {
    // TODO: cast to boolean
    return vscode.extensions.getExtension("ms-python.python");
}

/**
 * Extract a version number from a string.
 *
 * The version will be inside the path name for the extension (eg: virgilsisoe.nuke-tools-0.3.0)
 *
 * @param path - path like string of the stubs path inside package path.
 * @returns
 */
export function extractVersion(path: string) {
    const match = path.match(/virgilsisoe.nuke-tools-(.+?)\//);
    if (match) {
        return match[1];
    }
    return undefined;
}

/**
 * Update `python.analysis.extraPath`.
 *
 * Update configuration value only if value is not present or the version is lower
 * than the current version. Note: The update is made by reference.
 *
 * @param extraPaths - The `python.analysis.extraPaths` array object.
 * @param stubsPath - the stubs path to add in the `extraPaths` configuration.
 */
export function updateAnalysisPath(extraPaths: string[], stubsPath: string) {
    let alreadyAdded = false;

    for (const path of extraPaths) {
        const versionMatch = extractVersion(path);

        if (versionMatch) {
            // extract version from current stubs path is mostly needed for testing.
            if (versionMatch < extractVersion(stubsPath)!) {
                const index = extraPaths.indexOf(path);
                extraPaths[index] = stubsPath;
            }
            alreadyAdded = true;
        }
    }

    // first time does not match the condition above
    if (!alreadyAdded) {
        extraPaths.push(stubsPath);
    }
}

/**
 * Add stubs folder path to workspace settings `python.analysis.extraPaths`.
 * If path is already present, do nothing.
 */
export function addStubsPath(): boolean {
    if (!isPythonInstalled()) {
        vscode.window.showErrorMessage("Python extension is not installed.");
        return false;
    }

    const stubsPath = getStubsPath();

    const config = vscode.workspace.getConfiguration("python.analysis");
    const extraPaths = config.get("extraPaths") as Array<string>;

    updateAnalysisPath(extraPaths, stubsPath);
    config.update("extraPaths", extraPaths);
    return true;
}
