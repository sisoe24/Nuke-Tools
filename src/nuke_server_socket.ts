import * as vscode from "vscode";
import * as path from "path";
import * as fsExtra from "fs-extra";
import * as fs from "fs";

import * as utils from "./utils";

/**
 * Add NukeServerSocket to the .nuke folder and import it inside the menu.py
 */
export function addNss(): void {
    const destination = path.join(utils.nukeToolsDir, "NukeServerSocket");
    fsExtra.copySync(utils.getIncludedPath("NukeServerSocket"), destination, {
        overwrite: true,
    });

    const legacySrcFolder = path.join(destination, "src");
    if (fs.existsSync(legacySrcFolder)) {
        fsExtra.removeSync(legacySrcFolder);
    }

    utils.nukeMenuImport("from NukeTools import NukeServerSocket");

    const msg = `Added/Updated NukeServerSocket inside \`~/.nuke/NukeTools\`.
    You can now launch Nuke and find the plugin inside the Windows Custom panel.
    For more information please visit the official [README](https://github.com/sisoe24/NukeServerSocket#readme) page.
    `;
    vscode.window.showInformationMessage(msg);
}
