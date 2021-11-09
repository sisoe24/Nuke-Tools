import * as vscode from "vscode";
import * as executables from "./launch_executable";
import * as socket from "./socket";
import * as utils from "./utils";
import * as newUpdate from "./update_message";
import { addStubsPath } from "./stubs";

export function activate(context: vscode.ExtensionContext): void {
    newUpdate.showUpdateMessage(context);

    // XXX: this is now deprecated and will be removed in future version
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
            void executables.launchPromptExecutable();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.runCodeInsideNuke", () => {
            void socket.sendMessage();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.testRunInsideNuke", () => {
            void socket.sendDebugMessage();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.showNetworkAddresses", () => {
            vscode.window.showInformationMessage(socket.getAddresses());
        })
    );
}

// this method is called when your extension is deactivated
export function deactivate(): void {
    // XXX: how to force closing connection?
}
