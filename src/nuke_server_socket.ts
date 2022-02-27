import * as fs from "fs";
import * as path from "path";
import * as fsExtra from "fs-extra";

import * as utils from "./utils";

/**
 * Import NukeServerSocket inside the menu.py
 *
 * If file does not exists will create one and write to it, otherwise will append
 * at the end of it the statement: `import NukeServerSocket`
 */
function menuPyImport(): void {
    const menuPy = path.join(utils.nukeDir, "menu.py");
    const statement = "import NukeServerSocket";

    if (fs.existsSync(menuPy)) {
        if (!fs.readFileSync(menuPy, "utf-8").match(statement)) {
            fs.appendFileSync(menuPy, `\n${statement}\n`);
        }
    } else {
        fs.writeFileSync(menuPy, statement);
    }
}

/**
 * Add NukeServerSocket to the .nuke folder and import it inside the menu.py
 */
export function addNss(): void {
    const filename = "NukeServerSocket";
    const nssPath = utils.getIncludedPath(filename);
    fsExtra.copySync(nssPath, path.join(utils.nukeDir, filename), {
        overwrite: true,
    });
    menuPyImport();
}
