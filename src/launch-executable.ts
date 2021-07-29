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



// Execute command in terminal
export function execCommand(cmd: string) {

    // TODO: terminal name could be more descriptive

    if (utils.getConfiguration('nukeExecutable.options.restartInstance')) {
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name.startsWith('Nuke')) {
                terminal.dispose();
            }
        });
    }

    const terminal = vscode.window.createTerminal(require('path').posix.basename(cmd));

    console.log(cmd);

    terminal.sendText(cmd);
    terminal.show(true);

}
