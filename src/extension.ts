import * as vscode from "vscode";

import * as nuke from "./add_package";
import * as stubs from "./stubs";
import * as socket from "./socket";
import * as executables from "./launch_executable";
import * as nukeTemplate from "./create_project";

import { BlinkSnippets } from "./blinkscript/blink_snippet";
import { BlinkScriptFormat } from "./blinkscript/blink_format";
import { BlinkScriptCompletionProvider } from "./blinkscript/blink_completion";
import { checkPackageUpdates } from "./download_package";

import { NukeCompletionProvider } from "./nuke/completitions";
import { NukeNodesInspectorProvider } from "./nuke/nodes_tree";

import { showNotification } from "./notification";

function registerNodesInspectorCommands(context: vscode.ExtensionContext): void {
    const nukeProvider = new NukeNodesInspectorProvider();

    vscode.window.registerTreeDataProvider("nuke-tools", nukeProvider);

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.refreshNodes", () => nukeProvider.refresh())
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.syncNodes", () => nukeProvider.syncNodes())
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.on_itemClicked", (item) =>
            nukeProvider.itemClicked(item)
        )
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.addKnob", (item) => nukeProvider.addKnob(item))
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.syncKnob", (item) =>
            nukeProvider.syncKnob(item)
        )
    );
}

function registerBlinkScriptCommands(context: vscode.ExtensionContext): void {
    context.subscriptions.push(
        vscode.languages.registerDocumentFormattingEditProvider(
            "blinkscript",
            new BlinkScriptFormat()
        )
    );

    context.subscriptions.push(
        vscode.languages.registerCompletionItemProvider(
            "blinkscript",
            new BlinkScriptCompletionProvider()
        )
    );

    context.subscriptions.push(
        vscode.languages.registerCompletionItemProvider("blinkscript", new BlinkSnippets())
    );
}

function registerPackagesCommands(context: vscode.ExtensionContext): void {
    checkPackageUpdates(context);

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.forceUpdatePackages", () => {
            checkPackageUpdates(context, true);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.createPySide2Project", () => {
            nukeTemplate.createTemplate();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.addPythonStubs", () => {
            stubs.addStubs();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.addNukeServerSocket", () => {
            nuke.addNukeServerSocket();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.addVimDcc", () => {
            nuke.addVimDcc();
        })
    );
}

function registerExecutablesCommands(context: vscode.ExtensionContext): void {
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
}

export function activate(context: vscode.ExtensionContext): void {
    showNotification(context);

    registerNodesInspectorCommands(context);
    registerBlinkScriptCommands(context);
    registerPackagesCommands(context);
    registerExecutablesCommands(context);

    context.subscriptions.push(
        vscode.languages.registerCompletionItemProvider("python", new NukeCompletionProvider(), "(")
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
