import * as vscode from "vscode";
import * as path from "path";
import { readFileSync, createWriteStream } from "fs";

export const root = path.resolve(__dirname, "../../../");
export const packageFile = readFileSync(path.join(root, "package.json"), "utf-8");

export const demoPath = path.join(root, "demo");

/**
 * Get the package.json command names.
 *
 * @returns an array with all of the configurations options names.
 */
export function packageCommands(): string[] {
    const _packageCommands = JSON.parse(packageFile).contributes.commands;

    const commands: string[] = [];
    for (const command of _packageCommands) {
        commands.push(command.command);
    }
    return commands;
}

/**
 * Get the package.json configuration names.
 *
 * @returns an array with all of the configurations options names.
 */
export function packageConfigurations(): string[] {
    const _packageConfigs = JSON.parse(packageFile).contributes.configuration.properties;

    const configurations: string[] = [];
    for (const config of Object.keys(_packageConfigs)) {
        configurations.push(config.replace("nukeTools.", ""));
    }

    return configurations;
}

/**
 * Some tests will need to wait for vscode to register the actions. An example will
 * be creating/killing terminals and configuration update.
 *
 * @param milliseconds - time to sleep
 * @returns
 */
export const sleep = (milliseconds: number): Promise<unknown> => {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
};

/**
 * Configuration changes require async/await operation to let vscode register
 * the action.
 *
 * @param name - name of the configuration property to update.
 * @param value - the new value for the property.
 */
export async function updateConfig(name: string, value: unknown): Promise<void> {
    const config = vscode.workspace.getConfiguration("nukeTools");
    await config.update(name, value, vscode.ConfigurationTarget.Workspace);
}

/**
 * Open and focus a demo file.
 *
 * @param filename the name of a file to open.
 * @param line optional line number for the cursor to start at. Defaults to `0` which would be line `1`.
 * @param startChar optional position for the cursor to start at. Defaults to `0`
 * @param endChar optional position for the cursor to end at. If bigger than startChar,
 * will create a selection. Defaults to `0`
 */
export async function focusDemoFile(
    filename: string,
    line = 0,
    startChar = 0,
    endChar = 0
): Promise<vscode.TextEditor> {
    const filepath = path.join(demoPath, filename);
    const document = await vscode.workspace.openTextDocument(filepath);

    const startSelection = new vscode.Position(line, startChar);

    let endSelection = null;
    if (endChar) {
        endSelection = new vscode.Position(line, endChar);
    }
    const editor = await vscode.window.showTextDocument(document, {
        selection: new vscode.Selection(startSelection, endSelection || startSelection),
    });

    return editor;
}

/**
 * Create a demo file and write the content to it.
 *
 * If file doesn't exist, will get created, otherwise just updated with the new content.
 * Function will sleep 100ms before returning.
 *
 * @param filename name of the file demo to write the content to.
 * @param content  the content to write.
 */
export async function createDemoContent(filename: string, content: string): Promise<void> {
    const filepath = path.join(demoPath, filename);

    const file = createWriteStream(filepath);
    file.write(content);
    file.close();

    await sleep(200);
}

/**
 * Clean the settings.json file inside the demo folder.
 */
export function cleanSettings(): void {
    const file = path.join(".vscode", "settings.json");
    void createDemoContent(file, "{}");
}
