import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import * as cp from "child_process";

import * as vscode from "vscode";

import * as nuke from "./nuke";
import { getConfig } from "./config";
import { PackageIds, addPackage, packageMap } from "./packages";

/**
 * The placeholders data.
 *
 * All placeholders should start and end with double underscore: __value__
 */
export type PlaceHolders = {
    [key: string]: string;
};

/**
 * Ask user to fill the data that we are going to use to replace the placeholders
 * inside the pyside2 template project.
 *
 * @returns a placeholders object.
 */
export async function askUser(): Promise<PlaceHolders> {
    const projectName = (await vscode.window.showInputBox({
        title: "Project Name",
        value: "Project Name",
    })) as string;

    const projectPython = (await vscode.window.showInputBox({
        title: "Python version",
        value: (getConfig("pysideTemplate.pythonVersion") as string) || "~3.7.7",
    })) as string;

    const projectPySide = (await vscode.window.showInputBox({
        title: "PySide2 Version",
        placeHolder: "Version of PySide2",
        value: (getConfig("pysideTemplate.pysideVersion") as string) || "5.12.2",
    })) as string;

    const slug = (name: string) => {
        return name.replace(/\s/g, "").toLowerCase();
    };

    const placeholders: PlaceHolders = {};

    placeholders.__projectName__ = projectName;
    placeholders.__projectPython__ = projectPython;
    placeholders.__projectPySide__ = projectPySide;
    placeholders.__author__ = os.userInfo().username;
    placeholders.__projectSlug__ = slug(placeholders.__projectName__);
    placeholders.__authorSlug__ = slug(placeholders.__author__);
    placeholders.__githubUser__ = cp.execSync("git config user.name").toString().trim();
    placeholders.__email__ = placeholders.__author__ + "@email.com";

    return placeholders;
}

/**
 * Walk recursively a directory to get all of its files.
 *
 * @param dir Path for the directory to parse.
 * @returns A list of files
 */
const osWalk = function (dir: string): string[] {
    let results: string[] = [];

    fs.readdirSync(dir).forEach(function (file) {
        file = dir + path.sep + file;
        const stat = fs.statSync(file);
        if (stat && stat.isDirectory()) {
            /* Recurse into a subdirectory */
            results = results.concat(osWalk(file));
        } else {
            results.push(file);
        }
    });
    return results;
};

/**
 * Substitute placeholders values.
 *
 * @param files a list of files to apply substitution
 * @param placeholders placeholders object to replace
 */
export function substitutePlaceholders(files: string[], placeholders: PlaceHolders): void {
    for (const file of files) {
        let fileContent = fs.readFileSync(file, "utf-8");

        for (const [key, value] of Object.entries(placeholders)) {
            fileContent = fileContent.replace(RegExp(key, "g"), value);
        }
        fs.writeFileSync(file, fileContent);
    }
}

/**
 * Ask user to open the newly created pyside2 template in vscode.
 *
 * @param destination Path of the folder to open in vscode.
 */
async function openProjectFolder(destination: vscode.Uri): Promise<void> {
    const openProjectFolder = (await vscode.window.showQuickPick(["Yes", "No"], {
        title: "Open Project Folder?",
    })) as string;

    if (openProjectFolder === "Yes") {
        vscode.commands.executeCommand("vscode.openFolder", destination);
    }
}

/**
 * Ask user confirmation before importing the pyside2 template package inside the menu.py
 *
 * @param module The name of the module to import inside the menu.py
 */
async function importStatementMenu(module: string): Promise<void> {
    const loadNukeInit = (await vscode.window.showQuickPick(["Yes", "No"], {
        title: "Import into Nuke's menu.py?",
    })) as string;

    if (loadNukeInit === "Yes") {
        nuke.addMenuImport(`from NukeTools import ${module}`);
    }
}

/**
 * Create a PySide2 template Nuke plugin.
 */
export async function createTemplate(): Promise<void> {
    const userData = await askUser();

    const pkgData = packageMap.get(PackageIds.pySide2Template);
    if (!pkgData) {
        vscode.window.showErrorMessage(`NukeTools: Package not found: ${pkgData}`);
        return;
    }

    const originalDestination = pkgData.destination;
    pkgData.destination = path.join(pkgData.destination, userData.__projectSlug__);

    if (fs.existsSync(pkgData.destination)) {
        await vscode.window.showErrorMessage("Directory exists already.");
        return;
    }

    await addPackage(PackageIds.pySide2Template);

    substitutePlaceholders(osWalk(pkgData.destination), userData);

    await importStatementMenu(userData.__projectSlug__);
    await openProjectFolder(vscode.Uri.file(pkgData.destination));

    const msg = `Project creation completed. For more information, check 
    the official [README](https://github.com/sisoe24/pyside2-template#readme).
    `;

    vscode.window.showInformationMessage(msg);

    pkgData.destination = originalDestination;

}
