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

export function execDefaultCommand(cmd: string) {
    execCommand(defaultArgs(cmd));
}

export async function execOptionalCommand(cmd: string) {

    const optArgs = await vscode.window.showInputBox({
        ignoreFocusOut: true,
        placeHolder: "Optional arguments for current instance"
    });

    if (optArgs) {
        cmd += ' ' + optArgs;
    }

    execCommand(cmd);

}

// Execute commnad in temrinal
export function execCommand(cmd: string) {

    // TODO: terminal name could be more descriptive

    if (utils.getConfiguration('nukeExecutable.options.restartInstance')) {
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name.startsWith('Nuke')) {
                terminal.dispose();
            }
        });
    }

    if (!require('fs').existsSync(cmd)) {
        console.log('file path does not exist');
        vscode.window.showErrorMessage(`Cannot find path: ${cmd}.`);
        return;
    }

    // TODO: should also check if file is executable?
    // require('fs').statSync(cmd).mode will return a value that kind of helps

    const terminal = vscode.window.createTerminal(require('path').basename(cmd));

    terminal.sendText(cmd);
    terminal.show(true);

}
