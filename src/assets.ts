import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

const rootExtensionPath = vscode.extensions.getExtension("virgilsisoe.nuke-tools")
    ?.extensionPath as string;

export const ASSETS_PATH = path.join(rootExtensionPath, "assets");
if (!fs.existsSync(ASSETS_PATH)) {
    fs.mkdirSync(ASSETS_PATH);
}
export const pyside2Template = path.join(ASSETS_PATH, "pyside2-template");


/**
 * Get a path from the included directory.
 *
 * @returns the path to the included directory
 * @throws an error if the path could not be resolved
 */
export function getAssetPath(name: string): string {
    const file = path.join(rootExtensionPath, "assets", name);

    if (!fs.existsSync(file)) {
        throw new Error(`Could not find ${name} path.`);
    }

    return file;
}
