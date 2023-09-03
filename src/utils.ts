import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import * as vscode from "vscode";

export const nukeDir = path.join(os.homedir(), ".nuke");
export const nukeToolsDir = path.join(nukeDir, "NukeTools");

/**
 * Import NukeServerSocket inside the menu.py
 *
 * If file does not exists will create one and write to it, otherwise will append
 * the statement at the end.
 */
export function nukeMenuImport(statement: string): void {
    const menuPy = path.join(nukeDir, "menu.py");

    if (fs.existsSync(menuPy)) {
        if (!fs.readFileSync(menuPy, "utf-8").match(statement)) {
            fs.appendFileSync(menuPy, `\n${statement}\n`);
        }
    } else {
        fs.writeFileSync(menuPy, statement);
    }
}

export function extensionPath(): string {
    return vscode.extensions.getExtension("virgilsisoe.nuke-tools")?.extensionPath as string;
}

/**
 * Get a path from the included directory.
 *
 * @returns the path or undefined if couldn't resolve the path.
 */
export function getIncludedPath(directory: string, name: string): string {
    if (extensionPath()) {
        return path.join(extensionPath(), directory, name);
    }

    const msg = `Could not resolve ${name} path.`;
    vscode.window.showErrorMessage(msg);
    throw new Error(msg);
}

export function getIncludePath(name: string): string {
    return getIncludedPath("include", name);
}

export function getAssetsPath(name: string): string {
    return getIncludedPath("assets", name);
}
