import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

const rootExtensionPath = vscode.extensions.getExtension("virgilsisoe.nuke-tools")
    ?.extensionPath as string;

export const PATH = path.join(rootExtensionPath, "assets");
if (!fs.existsSync(PATH)) {
    fs.mkdirSync(PATH);
}

type Directories = "include" | "assets";

/**
 * Get a path from the included directory.
 *
 * @returns the path to the included directory
 * @throws an error if the path could not be resolved
 */
export function getPath(directory: Directories, name: string): string {
    const file = path.join(rootExtensionPath, directory, name);

    if (!fs.existsSync(file)) {
        const msg = `Could not find ${name} path.`;
        throw new Error(msg);
    }

    return file;
}
