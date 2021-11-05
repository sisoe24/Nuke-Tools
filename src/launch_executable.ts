import { basename } from "path";
import * as vscode from "vscode";
import * as utils from "./utils";

/**
 * ExecutablePath object class.
 */
export class ExecutablePath {
    args: string;

    /**
     * Init method for the ExecutablePath object.
     *
     * @param execPath - The path for the executable file.
     * @param terminalSuffix - A suffix for the terminal name that launches the
     * executable.
     */
    constructor(public execPath: string, public terminalSuffix: string) {
        this.terminalSuffix = terminalSuffix;
        this.execPath = execPath;
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
        return require("path").basename(this.execPath);
    }

    /**
     * Create the terminal name based on path basename and terminalSuffix argument.
     *
     * @returns the terminal name.
     */
    terminalName(): string {
        return `${this.basename()} ${this.terminalSuffix}`;
    }

    /**
     * Check if path exists. If not, will show an error message to user.
     *
     * @returns - True if does, False otherwise
     */
    isValid(): boolean {
        if (!require("fs").existsSync(this.execPath)) {
            vscode.window.showErrorMessage(`Cannot find path: ${this.execPath}.`);
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
        const path = this.verifyWindowsPath(this.quotePath(this.execPath));
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
    const terminalName = execPath.terminalName();

    const shouldRestart = utils.nukeToolsConfig("nukeExecutable.options.restartInstance");
    if (shouldRestart) {
        restartInstance(terminalName);
    }

    const terminal = vscode.window.createTerminal(terminalName);
    terminal.sendText(execPath.cliCmd());
    terminal.show(true);
}

/**
 * Launch executable. If executable path is not valid will do nothing.
 *
 * @param execObj
 */
export function launchExecutable(execObj: ExecutablePath) {
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
 * Launch primary executable from configuration.
 */
export function launchPrimaryExecutable() {
    const execObj = new ExecutablePath(
        utils.nukeToolsConfig(`nukeExecutable.primaryExecutablePath`),
        "Main"
    );
    launchExecutable(execObj);
}

/**
 * Launch secondary executable from configuration.
 */
export function launchSecondaryExecutable() {
    const execObj = new ExecutablePath(
        utils.nukeToolsConfig(`nukeExecutable.secondaryExecutablePath`),
        "Alt."
    );
    launchExecutable(execObj);
}

/**
 * Launch main executable with prompt for optional arguments.
 */
export async function launchPromptExecutable() {
    const execObj = new ExecutablePath(
        utils.nukeToolsConfig(`nukeExecutable.primaryExecutablePath`),
        "Opt."
    );

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
