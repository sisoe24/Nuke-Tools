// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import { privateEncrypt } from 'crypto';
import * as vscode from 'vscode';
import * as launchNuke from './launch-executable';
import * as socketClient from './client-socket';
import * as utils from "./utils";

// TODO: launch executable from different path than vscode workspace folder
// TODO: add create pyside plugin template
// TODO: restart Nuke plugin by checking the Widget name?
// TODO: colored output
// TODO: auto completion?


export function activate(context: vscode.ExtensionContext) {

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.launchNuke', () => {
        const execPath = utils.getExecutable('primaryExecutablePath');

        if (execPath) {
            launchNuke.execDefaultCommand(execPath, ' Main');
        };

    }));

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.launchNukeAlt', () => {
        const execPath = utils.getExecutable('secondaryExecutablePath');

        if (execPath) {
            launchNuke.execDefaultCommand(execPath, ' Alt.');
        };
    }));

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.launchNukeOptArgs', () => {
        const execPath = utils.getExecutable('primaryExecutablePath');

        if (execPath) {
            launchNuke.execOptionalCommand(execPath);
        };
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

        const data = {
            'file': editor.document.fileName,
            'text': editor.document.getText()
        };

        socketClient.sendText(JSON.stringify(data));

    }));

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.testRunInsideNuke', () => {
        socketClient.sendTestMessage();
    }));

    context.subscriptions.push(vscode.commands.registerCommand('nuke-tools.showNetworkAddresses', () => {
        vscode.window.showInformationMessage(socketClient.getAddresses());
    }));

}

// this method is called when your extension is deactivated
export function deactivate() {
    // TODO: should force closing connection just in case?
}

