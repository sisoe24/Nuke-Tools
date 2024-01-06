import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import * as vscode from "vscode";
import * as fsExtra from "fs-extra";
import * as assets from "./assets";

export const nukeDir = path.join(os.homedir(), ".nuke");
export const nssConfigJSON = path.join(nukeDir, "nukeserversocket.json");
export const nssConfigIni = path.join(nukeDir, "NukeServerSocket.ini");
export const nukeToolsDir = path.join(nukeDir, "NukeTools");
export const pythonStubsDir = path.join(nukeToolsDir, "stubs");
if (!fs.existsSync(pythonStubsDir)) {
    fs.mkdirSync(pythonStubsDir);
}

export function getNssConfig(value: string, defaultValue: string): string {
    if (fs.existsSync(nssConfigJSON)) {
        const fileContent = fs.readFileSync(nssConfigJSON, "utf-8");
        return JSON.parse(fileContent)[value] || defaultValue;
    }

    // Legacy support for NukeServerSocket.ini
    if (fs.existsSync(nssConfigIni)) {
        const fileContent = fs.readFileSync(nssConfigIni, "utf-8");
        const match = new RegExp(`${value}=(.+)`).exec(fileContent);
        if (match) {
            return match[1];
        }
    }

    return defaultValue;
}
/**
 * Write the import statement to the `menu.py` file. If the file doesn't exist, it will be created.
 *
 * @param text the text to write (e.g. `from NukeTools import NukeServerSocket`)
 */
export function writeMenuImport(text: string): void {
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

/**
 * Add NukeServerSocket to the .nuke folder and import it inside the menu.py
 */
export function addNukeServerSocket(): void {
    const destination = path.join(nukeToolsDir, "NukeServerSocket");
    fsExtra.copySync(assets.getPath("assets", "NukeServerSocket"), destination, {
        overwrite: true,
    });

    const legacySrcFolder = path.join(destination, "src");
    if (fs.existsSync(legacySrcFolder)) {
        fsExtra.removeSync(legacySrcFolder);
    }

    writeMenuImport("from NukeTools import NukeServerSocket\nNukeServerSocket.install_nuke()");

    const msg = `Added/Updated NukeServerSocket inside \`~/.nuke/NukeTools\`.
    You can now launch Nuke and find the plugin inside the Windows Custom panel.
    For more information please visit the official [README](https://github.com/sisoe24/NukeServerSocket#readme) page.
    `;
    vscode.window.showInformationMessage(msg);
}

/**
 * Add vimdcc to the .nuke folder and import it inside the menu.py
 */
export function addVimDcc(): void {
    const destination = path.join(nukeToolsDir, "vimdcc");
    fsExtra.copySync(assets.getPath("assets", "vimdcc"), destination, {
        overwrite: true,
    });

    writeMenuImport("from NukeTools.vimdcc import vimdcc\nvimdcc.install_nuke()");

    const msg = "Added/Updated VimDcc inside `~/.nuke/NukeTools`.";
    vscode.window.showInformationMessage(msg);
}
