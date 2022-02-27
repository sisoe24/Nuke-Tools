import * as vscode from "vscode";
import * as os from "os";
import * as path from "path";

export const nukeDir = path.join(os.homedir(), ".nuke");

/**
 * Get a path from the included directory.
 *
 * @returns the path or undefined if couldn't resolve the path.
 */
export function getIncludedPath(name: string): string {
    const extPath = vscode.extensions.getExtension("virgilsisoe.nuke-tools")?.extensionPath;
    if (extPath) {
        return path.join(extPath, "include", name);
    }

    const msg = `Could not resolve ${name} path.`;
    vscode.window.showErrorMessage(msg);
    throw new Error(msg);
}

/**
 * Get configuration property value.
 *
 * If property name is not found, throws an error.
 *
 * @param property - name of the configuration property to get.
 * @returns - the value of the property.
 */
export function nukeToolsConfig(property: string): unknown {
    const config = vscode.workspace.getConfiguration("nukeTools");
    const subConfig = config.get(property);

    if (typeof subConfig === "undefined") {
        throw new Error(`Configuration: ${property} doesn't exist`);
    }

    return subConfig;
}
