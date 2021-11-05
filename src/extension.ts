import * as vscode from "vscode";
import * as executables from "./launch_executable";
import * as socket from "./socket";
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
            executables.launchPrimaryExecutable();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.launchNukeAlt", () => {
            executables.launchSecondaryExecutable();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.launchNukeOptArgs", () => {
            executables.launchPromptExecutable();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.runInsideNuke", () => {
            socket.sendMessage();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.testRunInsideNuke", () => {
            socket.sendDebugMessage();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.showNetworkAddresses", () => {
            vscode.window.showInformationMessage(socket.getAddresses());
        })
    );
}

// this method is called when your extension is deactivated
export function deactivate() {
    // TODO: should force closing connection just in case?
}
