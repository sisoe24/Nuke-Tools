import * as path from "path";

import * as vscode from "vscode";

import * as stubs from "./stubs";
import * as nuke from "./nuke";
import * as socket from "./socket";
import { Version } from "./version";

import * as executables from "./launch_executable";
import * as nukeTemplate from "./create_project";

import { Version } from "./version";

import { BlinkSnippets } from "./blinkscript/blink_snippet";
import { BlinkScriptFormat } from "./blinkscript/blink_format";
import { BlinkScriptCompletionProvider } from "./blinkscript/blink_completion";

import { NukeCompletionProvider } from "./nuke/completitions";
import { NukeNodesInspectorProvider } from "./nuke/nodes_tree";

import { showNotification } from "./notification";
import { fetchPackagesLatestVersion } from "./fetch_packages";
import { initializePackageLog } from "./packages";
import { getConfig } from "./config";

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
    const addExtras: Record<string, () => void> = {
        pysideTemplate: nukeTemplate.createTemplate,
        pythonStubs: stubs.addStubs,
        nukeServerSocket: nuke.addNukeServerSocket,
        vimDcc: nuke.addVimDcc,
    };

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.addPackages", () => {
            const picker = vscode.window.createQuickPick();
            picker.items = Object.keys(addExtras).map((key) => {
                return {
                    label: key,
                };
            });

            picker.onDidChangeSelection((selection) => {
                if (selection[0]) {
                    addExtras[selection[0].label]();
                    picker.hide();
                }
            });

            picker.onDidHide(() => picker.dispose());
            picker.show();
        })
    );
}

function registerExtraCommands(context: vscode.ExtensionContext): void {
    const extras: Record<string, () => void> = {
        clearPackagesCache: () => {
            initializePackageLog();
            fetchPackagesLatestVersion();
            vscode.window.showInformationMessage("Packages cached cleared.");
        },
        testRunInsideNuke: () => {
            void socket.sendDebugMessage();
        },
        showNetworkAddresses: () => {
            vscode.window.showInformationMessage(socket.getAddresses());
        },
    };

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.extras", () => {
            const picker = vscode.window.createQuickPick();
            picker.items = Object.keys(extras).map((key) => {
                return {
                    label: key,
                };
            });

            picker.onDidChangeSelection((selection) => {
                if (selection[0]) {
                    extras[selection[0].label]();
                    picker.hide();
                }
            });

            picker.onDidHide(() => picker.dispose());
            picker.show();
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
        vscode.commands.registerCommand("nuke-tools.launchNukeOptArgs", () => {
            void executables.launchPromptExecutable();
        })
    );

    const nukeExecutables = getConfig("executablesMap");

    if (nukeExecutables) {
        for (const [name, config] of Object.entries(nukeExecutables)) {
            context.subscriptions.push(
                vscode.commands.registerCommand(`nuke-tools.${name}`, () => {
                    executables.launchExecutable(name, config);
                })
            );
        }
    }

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.showExecutables", () => {
            const picker = vscode.window.createQuickPick();

            picker.items = Object.keys(nukeExecutables).map((key) => {
                const executable = nukeExecutables[key];
                return {
                    label: key,
                    description: executable.args,
                    detail: executable.bin,
                };
            });

            picker.onDidChangeSelection((selection) => {
                if (selection[0]) {
                    executables.launchExecutable(
                        selection[0].label,
                        nukeExecutables[selection[0].label]
                    );
                    picker.hide();
                }
            });

            picker.onDidHide(() => picker.dispose());
            picker.show();
        })
    );
}

export function activate(context: vscode.ExtensionContext): void {
    Version.update(context);

    fetchPackagesLatestVersion();

    showNotification(context);

    registerNodesInspectorCommands(context);
    registerBlinkScriptCommands(context);
    registerPackagesCommands(context);
    registerExecutablesCommands(context);
    registerExtraCommands(context);

    context.subscriptions.push(
        vscode.languages.registerCompletionItemProvider("python", new NukeCompletionProvider(), "(")
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.runCodeInsideNuke", () => {
            void socket.sendMessage();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("nuke-tools.openNukeScript", () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return null;
            }
            const file = editor.document.fileName;

            if (file === null || !file.endsWith(".nk")) {
                vscode.window.showWarningMessage("Not a Nuke script (.nk)");
                return;
            }

            executables.launchExecutable(path.basename(file), {
                bin: getConfig("executablePath"),
                args: file,
            });
        })
    );
}
