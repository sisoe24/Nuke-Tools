import * as vscode from "vscode";
import * as executables from "./launch_executable";
import * as socketClient from "./socket";
import * as utils from "./utils";
import * as newUpdate from "./update_message";
import { addStubsPath } from "./stubs";

export function activate(context: vscode.ExtensionContext) {
    newUpdate.showUpdateMessage(context);

    // Add stubs automatically if config is enabled
    if (utils.nukeToolsConfig("other.autoAddStubsPath")) {
        addStubsPath();
    }

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.addPythonStubs", () => {
            addStubsPath();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.launchNuke", () => {
            executables.launchExecutable("primaryExecutablePath");
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.launchNukeAlt", () => {
            executables.launchExecutable("secondaryExecutablePath");
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.launchNukeOptArgs", () => {
            executables.launchExecutablePrompt();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.runInsideNuke", () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return;
            }

            if (editor.document.uri.scheme === "output") {
                vscode.window.showInformationMessage(
                    "You currently have the Output window in focus. Return the focus on the text editor."
                );
                return;
            }

            const data = {
                file: editor.document.fileName,
                text: editor.document.getText(),
            };

            socketClient.sendText(JSON.stringify(data));
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.testRunInsideNuke", () => {
            socketClient.sendDebugMessage();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand(
            "nuke-tools.showNetworkAddresses",
            () => {
                vscode.window.showInformationMessage(
                    socketClient.getAddresses()
                );
            }
        )
    );
}

// this method is called when your extension is deactivated
export function deactivate() {
    // TODO: should force closing connection just in case?
}
