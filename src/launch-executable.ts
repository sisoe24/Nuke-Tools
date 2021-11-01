import * as vscode from "vscode";
import * as utils from "./utils";

const config = vscode.workspace.getConfiguration(`nukeTools`);

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
     * @param {string} path - path like string to quote.
     * @returns {string} - the quoted path.
     */
    quotePath(path: string): string {
        return `"${path}"`;
    }

    /**
     * If system is Windows should require the & operator.
     *
     * eg. `& '/path/app name/bin'`
     *
     * @param {string} path - path like string to insert the `&` operator.
     * @returns {string} - string like path.
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
     * @returns {string} - base name of the executable path.
     */
    basename(): string {
        return require("path").basename(this.execName);
    }

    /**
     * Check if path exists. If not, will show an error message to user.
     *
     * @returns {boolean} - True if does, False otherwise
     */
    isValid(): boolean {
        if (!require("fs").existsSync(this.execName)) {
            // TODO: replace console log with log to file
            console.log("file path does not exist");

            vscode.window.showErrorMessage(
                `Cannot find path: ${this.execName}.`
            );
            return false;
        }
        return true;
    }

    /**
     *  Create the cli command to be executed inside the terminal.
     *
     * @returns {string} - string like command for the terminal.
     */
    cliCmd(): string {
        this.execName = this.verifyWindowsPath(this.quotePath(this.execName));
        return `${this.execName} ${this.args}`.trim();
    }
}

/**
 * Get the executable name and returns its path after it has been validated.
 *
 * @param {string} execName - name of the executable from the settings (eg: primaryExecutablePath or secondaryExecutablePath)
 * @returns {ExecutablePath} - ExecutablePath object.
 */
export function getExecutable(execName: string): ExecutablePath {
    const execPath = config.get(`nukeExecutable.${execName}`);

    if (!execPath) {
        throw new Error(`Executable name not found: ${execName}`);
    }

    return new ExecutablePath(execPath as string);
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
 * @param {string} cmd - the command to execute.
 * @param {string} suffix - a suffix name to add to the terminal instance name.
 */
export function execCommand(execPath: ExecutablePath) {
    const basename = execPath.basename();

    const shouldRestart = config.get<boolean>(
        "nukeExecutable.options.restartInstance"
    );
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
    const execPath = getExecutable(execName);

    if (execPath.isValid()) {
        const defaultArgs = config.get<string>(
            "nukeExecutable.options.defaultCommandLineArguments"
        );

        if (defaultArgs) {
            execPath.args = defaultArgs;
        }
        execCommand(execPath);
    }
}

/**
 * Launch main executable with prompt for optional arguments. If executable path
 * is not valid will do nothing.
 *
 */
export async function launchExecutablePrompt() {
    let execPath = getExecutable("primaryExecutablePath");

    if (execPath.isValid()) {
        const optArgs = await vscode.window.showInputBox({
            ignoreFocusOut: true,
            placeHolder: "Optional arguments for current instance",
        });

        if (optArgs) {
            execPath.args = optArgs;
        }
        execCommand(execPath);
    }
}
