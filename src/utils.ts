import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import * as vscode from "vscode";

export const nukeDir = path.join(os.homedir(), ".nuke");
export const nukeToolsDir = path.join(nukeDir, "NukeTools");
const rootExtensionPath = vscode.extensions.getExtension("virgilsisoe.nuke-tools")
    ?.extensionPath as string;

export const assetsPath = path.join(rootExtensionPath, "assets");
if (!fs.existsSync(assetsPath)) {
    fs.mkdirSync(assetsPath);
}

/**
 * Write the import statement to the `menu.py` file. If the file doesn't exist, it will be created.
 *
 * @param text the text to write (e.g. `from NukeTools import NukeServerSocket`)
 */
export function writeImport(text: string): void {
    const menuPy = path.join(nukeDir, "menu.py");

    if (fs.existsSync(menuPy)) {
        const fileContent = fs.readFileSync(menuPy, "utf-8");
        if (!fileContent.includes(text)) {
            fs.appendFileSync(menuPy, `\n${text}\n`);
        }
    } else {
        fs.writeFileSync(menuPy, text);
    }
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
