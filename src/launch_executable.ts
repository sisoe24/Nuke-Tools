import * as vscode from "vscode";
import * as utils from "./utils";

/**
 * ExecutablePath object class.
 */
export class ExecutablePath {
    args: string;

    constructor(public execName: string) {
        if (!execName) {
        }
        this.execName = execName;
        this.args = "";
    }

    /**
     * Quote path in case it has spaces.
     *
     * @param path - path like string to quote.
     * @returns - the quoted path.
     */
    quotePath(path: string): string {
        return `"${path}"`;
    }

    /**
     * If system is Windows should require the & operator.
     *
     * eg. `& '/path/app name/bin'`
     *
     * @param path - path like string to insert the `&` operator.
     * @returns - string like path.
     */
    verifyWindowsPath(path: string): string {
        if (require("os").type() === "Windows_NT") {
            path = `& ${path}`;
        }
        return path;
    }

    /**
     * Get the basename of the executable path.
     *
     * @returns  - base name of the executable path.
     */
    basename(): string {
        return require("path").basename(this.execName);
    }

    /**
     * Check if path exists. If not, will show an error message to user.
     *
     * @returns - True if does, False otherwise
     */
    isValid(): boolean {
        if (!require("fs").existsSync(this.execName)) {
            vscode.window.showErrorMessage(`Cannot find path: ${this.execName}.`);
            return false;
        }
        return true;
    }

    /**
     *  Create the cli command to be executed inside the terminal.
     *
     * @returns  - string like command for the terminal.
     */
    cliCmd(): string {
        const path = this.verifyWindowsPath(this.quotePath(this.execName));
        return `${path} ${this.args}`.trim();
    }
}

/**
 * Restart the terminal instance instead of creating new ones.
 *
 * @param name - name of the terminal to dispose.
 */
export function restartInstance(name: string) {
    vscode.window.terminals.forEach((terminal) => {
        if (terminal.name === name) {
            terminal.dispose();
        }
    });
}

/**
 * Execute the command in the terminal. Before executing the command, if restartInstance
 * is enabled, will dispose of the previous terminal instance.
 *
 * @param cmd - the command to execute.
 * @param suffix - a suffix name to add to the terminal instance name.
 */
export function execCommand(execPath: ExecutablePath) {
    const basename = execPath.basename();

    // TODO: add suffix to terminal
    const shouldRestart = utils.nukeToolsConfig("nukeExecutable.options.restartInstance");
    if (shouldRestart) {
        restartInstance(basename);
    }

    const terminal = vscode.window.createTerminal(basename);
    terminal.sendText(execPath.cliCmd());
    terminal.show(true);
}

/**
 * Launch executable. If executable path is not valid will do nothing.
 *
 * @param execName
 * @param suffix
 */
export function launchExecutable(execName: string) {
    const execObj = new ExecutablePath(execName);

    if (execObj.isValid()) {
        const defaultArgs = utils.nukeToolsConfig(
            "nukeExecutable.options.defaultCommandLineArguments"
        );

        if (defaultArgs) {
            execObj.args = defaultArgs;
        }
        execCommand(execObj);
    }
    return execObj;
}

/**
 * Launch main executable with prompt for optional arguments.
 *
 * If executable path is not valid will do nothing.
 *
 */
export async function launchExecutablePrompt(execName: string) {
    const execObj = new ExecutablePath(execName);

    if (execObj.isValid()) {
        const optArgs = await vscode.window.showInputBox({
            ignoreFocusOut: true,
            placeHolder: "Optional arguments for current instance",
        });

        if (optArgs) {
            execObj.args = optArgs;
        }
        execCommand(execObj);
    }
}
