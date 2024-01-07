import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import * as vscode from "vscode";
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

export function addMenuImport(importText: string): void {
    const menuPy = path.join(nukeDir, "menu.py");

    if (fs.existsSync(menuPy)) {
        const fileContent = fs.readFileSync(menuPy, "utf-8");
        if (!fileContent.includes(importText)) {
            fs.appendFileSync(menuPy, `\n${importText}\n`);
        }
    } else {
        fs.writeFileSync(menuPy, importText);
    }
}

async function addPackageToNukeTools(packageName: string): Promise<void> {
    const destination = path.join(nukeToolsDir, packageName);
    if (fs.existsSync(destination)) {
        fs.rmSync(destination, { recursive: true });
    }

    await vscode.workspace.fs.copy(
        vscode.Uri.file(assets.getAssetPath(packageName)),
        vscode.Uri.file(path.join(nukeToolsDir, packageName))
    );

    vscode.window.showInformationMessage(`Added/Updated ${packageName} in ~/.nuke/NukeTools.`);
}

/**
 * Add NukeServerSocket to the .nuke folder and import it inside the menu.py
 */
export function addNukeServerSocket(): void {
    addPackageToNukeTools("NukeServerSocket");
    addMenuImport(
        "from NukeTools.NukeServerSocket import nukeserversocket\nnukeserversocket.install_nuke()"
    );
}

/**
 * Add vimdcc to the .nuke folder and import it inside the menu.py
 */
export function addVimDcc(): void {
    addPackageToNukeTools("vimdcc");
    addMenuImport("from NukeTools.vimdcc import vimdcc\nvimdcc.install_nuke()");
}
