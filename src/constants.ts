import * as os from "os";
import * as path from "path";
import * as vscode from "vscode";


export const NUKE_DIR = path.join(os.homedir(), ".nuke");
export const NUKE_TOOLS_DIR = path.join(NUKE_DIR, "NukeTools");

export const PACKAGE_ROOT  = vscode.extensions.getExtension("virgilsisoe.nuke-tools")
    ?.extensionPath as string;

export const PACKAGE_RESOURCES_PATH = path.join(PACKAGE_ROOT, "resources");
