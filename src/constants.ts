import * as os from "os";
import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";


export const NUKE_DIR = path.join(os.homedir(), ".nuke");
export const NUKE_TOOLS_DIR = path.join(NUKE_DIR, "NukeTools");

export const PACKAGE_ROOT  = vscode.extensions.getExtension("virgilsisoe.nuke-tools")
    ?.extensionPath as string;

export const PACKAGE_RESOURCES_PATH = path.join(PACKAGE_ROOT, "resources");
export const ASSETS_PATH = path.join(PACKAGE_RESOURCES_PATH, "assets");
if (!fs.existsSync(ASSETS_PATH )) {
    fs.mkdirSync(ASSETS_PATH );
}

export const ASSETS_LOG_PATH = path.join(PACKAGE_RESOURCES_PATH, "included_assets.json");