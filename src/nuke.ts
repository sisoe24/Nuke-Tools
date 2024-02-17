import * as fs from "fs";
import * as os from "os";
import * as path from "path";

import * as packages from "./packages";

export function addMenuImport(importText: string): void {
    const menuPy = path.join(os.homedir(), ".nuke", "menu.py");

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
