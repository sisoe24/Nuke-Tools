// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import { privateEncrypt } from 'crypto';
import * as vscode from 'vscode';
import * as launchNuke from './launch-executable';
import * as socketClient from './socket-client';
import * as utils from "./utils";

// https://stackoverflow.com/questions/43007267/how-to-run-a-system-command-from-vscode-extension

// TODO: add create pyside plugin template
// TODO: restart Nuke plugin by checking the Widget name?
// TODO: colored output
// TODO: auto completion?


export function activate(context: vscode.ExtensionContext) {

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.launchNuke', () => {
        const execPath = utils.getConfiguration('nukeExecutable.primaryExecutablePath');
        launchNuke.execDefaultCommand(execPath);
    }));

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.launchNukeAlt', () => {
        const execPath = utils.getConfiguration('nukeExecutable.secondaryExecutablePath');
        launchNuke.execDefaultCommand(execPath);

    }));

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.launchNukeOptArgs', () => {
        const execPath = utils.getConfiguration('nukeExecutable.primaryExecutablePath');
        launchNuke.execOptionalCommand(execPath);
    }));

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.runInsideNuke', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) { return; }

        if (editor.document.uri.scheme === 'output') {
            vscode.window.showInformationMessage(
                'You currently have the Output window in focus. Return the focus on the text editor.'
            );
            return;
        }

        socketClient.sendText(editor.document.getText());

    }));

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.testRunInsideNuke', () => {

        const random = () => Math.round(Math.random() * 10);
        const r1 = random();
        const r2 = random();
        const sum = r1 * r2;

        const cmd = `from __future__ import print_function;result = ${sum};print("Hello from Vscode Test Client. ${r1} * ${r2} =", result)`;
        socketClient.sendText(cmd);

    }));

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.showNetworkAddresses', () => {
        vscode.window.showInformationMessage(socketClient.getAddresses());
    }));

}

// this method is called when your extension is deactivated
export function deactivate() { }
