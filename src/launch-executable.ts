import * as vscode from 'vscode';
import * as utils from "./utils";


// check for default arguments
export function defaultArgs(cmd: string): string {

    const defaultArgs = utils.getConfiguration('nukeExecutable.options.defaultCommandLineArguments');
    if (defaultArgs) {
        cmd += ' ' + defaultArgs;
    }
    return cmd;

}

export function execDefaultCommand(cmd: string, suffix: string) {
    execCommand(defaultArgs(cmd), suffix);
}

export async function execOptionalCommand(cmd: string) {

    const optArgs = await vscode.window.showInputBox({
        ignoreFocusOut: true,
        placeHolder: "Optional arguments for current instance"
    });

    if (optArgs) {
        cmd += ' ' + optArgs;
    }

    execCommand(cmd, ' Main');

}

// the cmd will be wrapped inside single quotes to avoid path splitting
// and basename will delete everything till the last quote but include optional arguments if any
// TODO: this has an undefined behaviour when there is an argument
function extractCmdBaseName(cmd: string): string {

    // example of what could return: Nuke13.0" -nc
    const baseNameCmd = require('path').basename(cmd);
    cmd = baseNameCmd.split('"')[0];
    return cmd;
}

// Execute command in terminal
export function execCommand(cmd: string, suffix: string) {

    const terminalTitle = extractCmdBaseName(cmd) + suffix;

    if (utils.getConfiguration('nukeExecutable.options.restartInstance')) {
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name === terminalTitle) {
                terminal.dispose();
            }
        });
    }

    const terminal = vscode.window.createTerminal(terminalTitle);
    terminal.sendText(cmd);
    terminal.show(true);

}
