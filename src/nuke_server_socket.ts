import * as path from "path";
import * as fsExtra from "fs-extra";

import * as utils from "./utils";
import { nukeMenuImport } from "./utils";

/**
 * Add NukeServerSocket to the .nuke folder and import it inside the menu.py
 */
export function addNss(): void {
    const filename = "NukeServerSocket";
    const nssPath = utils.getIncludedPath(filename);
    fsExtra.copySync(nssPath, path.join(utils.nukeDir, filename), {
        overwrite: true,
    });
    nukeMenuImport(`import ${filename}`);
}
