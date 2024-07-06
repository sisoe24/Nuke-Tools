import * as fs from "fs";
import * as path from "path";

import * as packages from "./packages";
import { NUKE_DIR } from "./constants";

const MENU_PY = path.join(NUKE_DIR, "menu.py");

/**
 * Add a menu import to the menu.py file in the .nuke folder.
 * 
 * Only adds the import if it doesn't already exist.
 * 
 * @param importText The import statement to add to the menu.py file.
 */
export function addMenuImport(importText: string): void {
    if (fs.existsSync(MENU_PY)) {
        const fileContent = fs.readFileSync(MENU_PY, "utf-8");
        if (!fileContent.includes(importText)) {
            fs.appendFileSync(MENU_PY, `\n${importText}\n`);
        }
    } else {
        fs.writeFileSync(MENU_PY, importText);
    }
}

/**
 * Cleanup the legacy NukeServerSocket import from the menu.py file. 
 * 
 * NukeServerSocket < 1.0.0 used to have a different import statement which is now deprecated
 * and should be removed from the menu.py file if it exists.
 */
function cleanupLegacyNukeServerSocket(): void {
    if (!fs.existsSync(MENU_PY)) {
        return;
    }

    const fileContent = fs.readFileSync(MENU_PY, "utf-8");

    const legacyImport = "from NukeTools import NukeServerSocket";

    if (!fileContent.includes(legacyImport)) {
        return;
    }

    fs.writeFileSync(MENU_PY, fileContent.replace(legacyImport, ""));
}

/**
 * Add nukeserversocket to the .nuke folder and import it inside the menu.py
 */
export function addNukeServerSocket(): void {
    cleanupLegacyNukeServerSocket();
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
