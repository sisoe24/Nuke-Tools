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

function addImport(name: string, text: string): void {
    const destination = path.join(nukeToolsDir, name);
    if (fs.existsSync(destination)) {
        fs.rmSync(destination, { recursive: true });
    }

    fsExtra.copySync(assets.getPath("assets", name), destination, {});

    const menuPy = path.join(nukeDir, "menu.py");

    if (fs.existsSync(menuPy)) {
        const fileContent = fs.readFileSync(menuPy, "utf-8");
        if (!fileContent.includes(text)) {
            fs.appendFileSync(menuPy, `\n${text}\n`);
        }
    } else {
        fs.writeFileSync(menuPy, text);
    }

    vscode.window.showInformationMessage(`Added/Updated ${name} in ~/.nuke/NukeTools.`);
}

/**
 * Add NukeServerSocket to the .nuke folder and import it inside the menu.py
 */
export function addNukeServerSocket(): void {
    addImport(
        "NukeServerSocket",
        "from NukeTools.NukeServerSocket import nukeserversocket\nnukeserversocket.install_nuke()"
    );
}

/**
 * Add vimdcc to the .nuke folder and import it inside the menu.py
 */
export function addVimDcc(): void {
    addImport("vimdcc", "from NukeTools.vimdcc import vimdcc\nvimdcc.install_nuke()");
}
