import * as vscode from "vscode";

import { PackageIds, addPackage } from "./packages";

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
export async function addStubs(): Promise<void> {
    if (!vscode.extensions.getExtension("ms-python.python")) {
        vscode.window.showErrorMessage(
            "Python extension is not installed. Could not add stubs path."
        );
        return;
    }

    const pkg = await addPackage(PackageIds.nukePythonStubs);
    if (!pkg) {
        vscode.window.showErrorMessage("Could not add stubs path.");
        return;
    }

    updatePythonExtraPaths(pkg.destination);

    vscode.window.showInformationMessage("Python stubs added.");
}
