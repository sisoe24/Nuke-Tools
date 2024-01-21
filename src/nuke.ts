import * as fs from "fs";
import * as os from "os";
import * as path from "path";

import * as packages from "./packages";

const NUKE_DIR = path.join(os.homedir(), ".nuke");

export function getNssConfig(value: string, defaultValue: string): string {
    const nssConfigJSON = path.join(NUKE_DIR, "nukeserversocket.json");
    const nssConfigIni = path.join(NUKE_DIR, "NukeServerSocket.ini");

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
    const menuPy = path.join(NUKE_DIR, "menu.py");

    if (fs.existsSync(menuPy)) {
        const fileContent = fs.readFileSync(menuPy, "utf-8");
        if (!fileContent.includes(importText)) {
            fs.appendFileSync(menuPy, `\n${importText}\n`);
        }
    } else {
        fs.writeFileSync(menuPy, importText);
    }
}

/**
 * Add nukeserversocket to the .nuke folder and import it inside the menu.py
 */
export function addNukeServerSocket(): void {
    packages.addPackage(packages.PackageIds.nukeServerSocket);
    addMenuImport(
        "from NukeTools.nukeserversocket import nukeserversocket\nnukeserversocket.install_nuke()"
    );
}

/**
 * Add vimdcc to the .nuke folder and import it inside the menu.py
 */
export function addVimDcc(): void {
    packages.addPackage(packages.PackageIds.vimdcc);
    addMenuImport("from NukeTools.vimdcc import vimdcc\nvimdcc.install_nuke()");
}
