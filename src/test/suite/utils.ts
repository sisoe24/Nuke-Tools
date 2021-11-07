import * as vscode from "vscode";
import * as path from "path";
import { writeFileSync, existsSync } from "fs";

/**
 * Some tests will need to wait for vscode to register the actions. An example will
 * be creating/killing terminals and configuration update.
 *
 * @param milliseconds - time to sleep
 * @returns
 */
export const sleep = (milliseconds: number) => {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
};

/**
 * Configuration changes require async/await operation to let vscode register
 * the action.
 *
 * @param name - name of the configuration property to update.
 * @param value - the new value for the property.
 */
export async function updateConfig(name: string, value: unknown) {
    // vscode.extensions.getExtension("virgilsisoe.nuke-tools")?.activate();
    const nukeTools = vscode.workspace.getConfiguration("nukeTools");
    return nukeTools.update(name, value, vscode.ConfigurationTarget.Workspace);
}

/**
 * Get the tmp folder path in rootDir.
 *
 * @returns path of the tmp directory
 */
export function tmpFolder(): string {
    const cwd = vscode.extensions.getExtension("virgilsisoe.nuke-tools")!.extensionPath;
    return path.join(cwd, "tmp");
}

/**
 * Clean the settings.json file inside the temporary folder.
 *
 * Method will wait for 200ms before completing. This is to give enough time to
 * vscode to register the changes.
 */
export async function cleanSettings() {
    const settings = path.join(tmpFolder(), ".vscode", "settings.json");
    if (existsSync(settings)) {
        writeFileSync(settings, "{}");
    }
    await sleep(200);
}
