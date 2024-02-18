import * as fs from "fs";
import * as path from "path";

import * as vscode from "vscode";

import * as nuke from "./nuke";
import { PackageIds, addPackage, packageMap } from "./packages";

/**
 * Ask user to fill the data that we are going to use to replace the placeholders
 * inside the pyside2 template project.
 *
 * @returns a placeholders object.
 */
export async function askUser(): Promise<string> {
    const projectName = (await vscode.window.showInputBox({
        title: "Project Name",
        value: "Project Name",
    })) as string;

    return projectName.replace(/\s/g, "").toLowerCase();
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
 * @param projectSlug the name of the project to use as substitution
 */
export function substitutePlaceholders(files: string[], projectSlug: string): void {
    for (const file of files) {
        let fileContent = fs.readFileSync(file, "utf-8");
        fileContent = fileContent.replace(RegExp("projectslug", "g"), projectSlug);
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
    const projectSlug = await askUser();

    const pkgData = packageMap.get(PackageIds.pySide2Template);
    if (!pkgData) {
        vscode.window.showErrorMessage(`NukeTools: Package not found: ${pkgData}`);
        return;
    }

    const destination = path.join(pkgData.destination, projectSlug);

    if (fs.existsSync(destination)) {
        await vscode.window.showErrorMessage("Directory exists already.");
        return;
    }

    await addPackage(PackageIds.pySide2Template, destination);

    substitutePlaceholders(osWalk(destination), projectSlug);

    fs.renameSync(path.join(destination, "projectslug"), path.join(destination, projectSlug));

    await importStatementMenu(projectSlug);
    await openProjectFolder(vscode.Uri.file(destination));

    vscode.window.showInformationMessage(
        `Project ${projectSlug} created. For more information, please read
        the official [README](https://github.com/sisoe24/pyside2-template#readme).`
    );
}
