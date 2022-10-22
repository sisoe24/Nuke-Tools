import * as vscode from "vscode";

import * as fs from "fs";
import * as os from "os";
import * as path from "path";

import { nukeMenuImport } from "./nuke_server_socket";
import { getIncludedPath, nukeToolsConfig } from "./utils";

export type PlaceHolders = {
    [key: string]: string;
};

/**
 * Ask user to fill some value that are going to be used to replace some
 * placeholders when creating the Spoon template.
 *
 * @returns a placeholders object.
 */
export async function askUser(): Promise<PlaceHolders> {
    const projectName = (await vscode.window.showInputBox({
        title: "Project Name",
        value: "Project Name",
    })) as string;

    const projectDescription = (await vscode.window.showInputBox({
        title: "Project Description",
        value: "Project Description",
    })) as string;

    // const config = nukeToolsConfig("pysideTemplate") as { [key: string]: string };
    const projectPython = (await vscode.window.showInputBox({
        title: "Python version",
        value: (nukeToolsConfig("pysideTemplate.pythonVersion") as string) || ">=3.6, <=3.7.7",
    })) as string;

    const projectPySide = (await vscode.window.showInputBox({
        title: "PySide2 Version",
        placeHolder: "Version of PySide2",
        value: (nukeToolsConfig("pysideTemplate.pysideVersion") as string) || "5.12.2",
    })) as string;

    const projectAuthor = (await vscode.window.showInputBox({
        title: "Project Author",
        value: os.userInfo().username,
    })) as string;

    const slug = (name: string) => {
        return name.replace(" ", "").toLowerCase();
    };

    const placeholders: PlaceHolders = {};

    placeholders.__projectName__ = projectName;
    placeholders.__projectDescription__ = projectDescription;
    placeholders.__projectPython__ = projectPython;
    placeholders.__projectPySide__ = projectPySide;
    placeholders.__author__ = projectAuthor;
    placeholders.__projectSlug__ = slug(placeholders.__projectName__);
    placeholders.__authorSlug__ = slug(placeholders.__author__);
    placeholders.__githubUser__ = placeholders.__author__ + "@email";
    placeholders.__email__ = placeholders.__author__ + "@email";

    return placeholders;
}

const osWalk = function (dir: string) {
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
 * Create the `init.lua` template file.
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

async function openProjectFolder(destination: vscode.Uri) {
    const openProjectFolder = (await vscode.window.showQuickPick(["Yes", "No"], {
        title: "Open Project Folder?",
    })) as string;

    if (openProjectFolder === "Yes") {
        vscode.commands.executeCommand("vscode.openFolder", destination);
    }
}

async function importStatementMenu(module: string) {
    const loadNukeInit = (await vscode.window.showQuickPick(["Yes", "No"], {
        title: "Import into Nuke's menu.py?",
    })) as string;

    if (loadNukeInit === "Yes") {
        nukeMenuImport(module);
    }
}

export async function createTemplate(): Promise<void> {
    const userData = await askUser();

    const projectPath = path.join(os.homedir(), ".nuke", "NukeTools");
    const destination = vscode.Uri.file(path.join(projectPath, userData.__projectSlug__));

    if (fs.existsSync(destination.fsPath)) {
        await vscode.window.showErrorMessage("Directory exists already.");
        return;
    }

    const source = vscode.Uri.file(getIncludedPath("pyside2-template"));
    await vscode.workspace.fs.copy(source, destination);

    const pythonFiles = osWalk(destination.fsPath);

    substitutePlaceholders(pythonFiles, userData);

    await importStatementMenu(userData.__projectSlug__);
    await openProjectFolder(destination);
}
