import * as vscode from "vscode";
import * as utils from "./utils";

const config = vscode.workspace.getConfiguration(`nukeTools`);

/**
 * Quote path in case it has spaces.
 *
 * @param {string} path - path like string to quote.
 * @returns {string} - the quoted path.
 */
function quotePath(path: string): string {
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
function verifyWindowsPath(path: string): string {
    if (require("os").type() === "Windows_NT") {
        path = `& ${path}`;
    }
    return path;
}

/**
 * Check if path exists. If not, will show an error message to user.
 *
 * @param {string} path - path to check if exists.
 * @returns {boolean} - True if does, False otherwise
 */
function pathExists(path: string): boolean {
    if (!require("fs").existsSync(path)) {
        // TODO: replace console log with log to file
        console.log("file path does not exist");

        vscode.window.showErrorMessage(`Cannot find path: ${path}.`);
        return false;
    }
    return true;
}

/**
 * Validate executable path.
 * 
 * If path exists, will check if current system is Windows and insert the & operator,
 * and quote it in cases of spaces. If path is not valid will return an empty string.
 *
 * @param {string} path - path like string to check.
 * @returns {string} - string like path is path exists or empty string if path
 * does not exists.
 */
function validatePath(path: string): string {
    // TODO: should also check if file is executable?
    // require('fs').statSync(exec).mode will return a value that kind of helps

    if (pathExists(path)) {
        return verifyWindowsPath(quotePath(path));
    }
    return "";
}

/**
 * Get the executable name and returns its path after it has been validated.
 *
 * @param {string} execName - name of the executable from the settings (eg: primaryExecutablePath or secondaryExecutablePath)
 * @returns {string} - string like path of the executable.
 */
export function getExecutable(execName: string): string {
    const execPath = config.get(`nukeExecutable.${execName}`) as string;
    return validatePath(execPath);
}

/**
 * Get cli arguments from settings and append them to the executable path.
 * Settings could be empty, in that case will do nothing.
 *
 * @param {string} path - executable path append the arguments.
 * @returns {string} - string like path.
 */
function appendArgs(path: string): string {
    const defaultArgs = utils.getConfiguration(
        "nukeExecutable.options.defaultCommandLineArguments"
    );
    if (defaultArgs) {
        path += " " + defaultArgs;
    }
    return path;
}

// the cmd will be wrapped inside single quotes to avoid path splitting
// and basename will delete everything till the last quote but include optional arguments if any
// TODO: this has an undefined behaviour when there is an argument
function extractExecBaseName(cmd: string): string {
    // example of what could return: Nuke13.0" -nc
    const baseNameCmd = require("path").basename(cmd);
    cmd = baseNameCmd.split('"')[0];
    return cmd;
}

/**
 * Restart the terminal instance instead of creating new ones.
 *
 * @param name - name of the terminal to dispose.
 */
function restartInstance(name: string) {
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
function execCommand(cmd: string, suffix: string) {
    const terminalTitle = extractExecBaseName(cmd) + suffix;

    const shouldRestart = config.get("nukeExecutable.options.restartInstance");
    if (shouldRestart) {
        restartInstance(terminalTitle);
    }

    const terminal = vscode.window.createTerminal(terminalTitle);
    terminal.sendText(cmd);
    terminal.show(true);
}

/**
 * Launch executable. If executable path is not valid will do nothing.
 *
 * @param execName
 * @param suffix
 */
export function launchExecutable(execName: string, suffix: string) {
    const execPath = getExecutable(execName);

    if (execPath) {
        execCommand(appendArgs(execPath), suffix);
    }
}

/**
 * Launch main executable with prompt for optional arguments. If executable path
 * is not valid will do nothing.
 *
 */
export async function launchExecutablePrompt() {
    let execPath = getExecutable("primaryExecutablePath");

    if (execPath) {
        const optArgs = await vscode.window.showInputBox({
            ignoreFocusOut: true,
            placeHolder: "Optional arguments for current instance",
        });

        if (optArgs) {
            execPath += " " + optArgs;
        }
        execCommand(execPath, " Main");
    }
}
