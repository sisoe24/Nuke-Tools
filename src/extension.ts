import * as vscode from 'vscode';
import * as launchNuke from './launch-executable';
import * as socketClient from './client-socket';
import * as utils from "./utils";
import * as newUpdate from './newUpdateMsg';

// TODO: launch executable from different path than vscode workspace folder
// TODO: add create pyside plugin template
// TODO: auto completion?
// TODO: remote debugging?

export function activate(context: vscode.ExtensionContext) {

    newUpdate.showUpdateMessage(context);

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
        const editor = vscode.window.activeTextEditor;
        if (!editor) { return; }
        console.log(editor.document);
    }));

}

// this method is called when your extension is deactivated
export function deactivate() {
    // TODO: should force closing connection just in case?
}
