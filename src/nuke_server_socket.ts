import * as vscode from "vscode";
import * as path from "path";
import * as fsExtra from "fs-extra";

import * as utils from "./utils";

/**
 * Add NukeServerSocket to the .nuke folder and import it inside the menu.py
 */
export function addNss(): void {
    const filename = "NukeServerSocket";
    const nssPath = utils.getIncludedPath(filename);
    fsExtra.copySync(nssPath, path.join(utils.nukeToolsDir, filename), {
        overwrite: true,
    });
    utils.nukeMenuImport(`from NukeTools import ${filename}`);

    const msg = `Added/Updated NukeServerSocket inside \`~/.nuke/NukeTools\`.
    You can now launch Nuke and find the plugin inside the Windows Custom panel.
    For more information please visit the official [README](https://github.com/sisoe24/NukeServerSocket#readme) page.
    `;
    vscode.window.showInformationMessage(msg);
}
