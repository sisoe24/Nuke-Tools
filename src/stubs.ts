import * as nuke from "./nuke";
import * as vscode from "vscode";

import { downloadStubs } from "./download_package";

/**
 * Check whether the Python extension is installed, as attempting to add the stubs
 * to analysis.extraPaths will fail if Python is not installed.
 *
 * @returns true if extension is installed, false otherwise.
 */
export function isPythonInstalled(): boolean {
    return Boolean(vscode.extensions.getExtension("ms-python.python"));
}

/**
 * Determine the configuration for extraPaths based on the current Python server.
 *
 *  - Pylance:  `python.analysis`
 *  - Jedi:  `python.autoComplete`
 *
 * @returns the settings name for the extra paths
 */
export function getPythonLspKey(): string {
    // when pythonServer is Default, we assume that Pylance is installed.
    const pythonServer = vscode.workspace.getConfiguration("python").get("languageServer");

    if (pythonServer === "Jedi") {
        return "python.autoComplete";
    }

    return "python.analysis";
}

/**
 * Update the python.analysis.extraPaths setting with the stubs path.
 *
 * @param nukeToolsStubsPath - path to the stubs directory
 *
 */
function updatePythonExtraPaths(nukeToolsStubsPath: string) {
    const config = vscode.workspace.getConfiguration(getPythonLspKey(), null);
    const extraPaths = config.get("extraPaths") as string[];

    if (!extraPaths.includes(nukeToolsStubsPath)) {
        extraPaths.push(nukeToolsStubsPath);
        config.update("extraPaths", extraPaths, vscode.ConfigurationTarget.Global);
    }
}

/**
 * Add the stubs path to the python.analysis.extraPaths setting.
 */
export function addStubs(): void {
    if (!isPythonInstalled()) {
        vscode.window.showErrorMessage(
            "Python extension is not installed. Could not add stubs path."
        );
        return;
    }

    downloadStubs(nuke.nukePythonStubsDir);
    updatePythonExtraPaths(nuke.nukePythonStubsDir);

    vscode.window.showInformationMessage("Python stubs added.");
}
