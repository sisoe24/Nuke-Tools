import * as os from "os";
import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

import { getConfig } from "./config";

/**
 * ExecutablePath object class.
 */
export class ExecutablePath {
    args: string;
    execPath: string;
    terminalSuffix: string;

    /**
     * Init method for the ExecutablePath object.
     *
     * @param execPath - The path for the executable file.
     * @param terminalSuffix - A suffix for the terminal name that launches the
     * executable.
     */
    constructor(execPath: string, terminalSuffix: string) {
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
        if (os.type() === "Windows_NT") {
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
        return path.basename(this.execPath);
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
        if (!fs.existsSync(this.execPath)) {
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
export function restartInstance(name: string): void {
    vscode.window.terminals.forEach((terminal) => {
        if (terminal.name === name) {
            terminal.dispose();
        }
    });
}

type EnvVars = { [key: string]: string };

/**
 * Concatenate the user's environment variables with the system's environment variables.
 *
 * @param userConfigVars EnvVars object containing the user's environment variables
 * return an EnvVars object containing the concatenated environment variables
 */
function concatEnv(userConfigVars: EnvVars): EnvVars {
    const env: EnvVars = {};

    for (const [k, v] of Object.entries(userConfigVars)) {
        const systemEnvVar = process.env[k];

        if (systemEnvVar) {
            env[k] = `${systemEnvVar}:${v}`;
        } else {
            env[k] = v;
        }

        // remove double colons just in case
        env[k] = env[k].replace(/::/g, ":");
    }

    return env;
}

/**
 * Stringify the environment variables into a string that can be used in the terminal.
 *
 * @param env EnvVars object containing the environment variables to stringify
 * @returns a string containing the environment variables
 */
function stringifyEnv(env: EnvVars): string {
    let envString = "";

    for (const [k, v] of Object.entries(env)) {
        envString += `${k}=${v} `;
    }

    return envString;
}
/**
 * Get the command line text to use when launching a nuke executable.
 *
 * Also tries to add env variables if it finds any in the settings
 *
 * @param execPath - ExecutablePath object.
 * @returns the command line text as a string.
 */
export function getCliCmd(execPath: ExecutablePath): string {
    const cliCmd = execPath.cliCmd();

    // TODO: add windows support.
    if (os.type() === "Windows_NT") {
        return cliCmd;
    }

    let env = getConfig("env.envVars") as EnvVars;

    if (getConfig("env.useSystemEnv") as boolean) {
        env = concatEnv(env);
    }

    const envString = stringifyEnv(env);

    return `${envString} ${cliCmd}`;
}

/**
 * Execute the command in the terminal. Before executing the command, if restartInstance
 * is enabled, will dispose of the previous terminal instance.
 *
 * @param execPath - ExecutablePath object.
 */
export function execCommand(execPath: ExecutablePath): void {
    const terminalName = execPath.terminalName();

    const shouldRestart = getConfig("nukeExecutable.options.restartInstance");
    if (shouldRestart) {
        restartInstance(terminalName);
    }

    const terminal = vscode.window.createTerminal(terminalName);

    terminal.sendText(getCliCmd(execPath));
    terminal.show(true);
}

/**
 * Launch executable. If executable path is not valid will do nothing.
 *
 * @param execObj - the executable path object to launch.
 * @returns - the executable path object created.
 */
export function launchExecutable(execObj: ExecutablePath): ExecutablePath {
    if (execObj.isValid()) {
        execCommand(execObj);
    }
    return execObj;
}

/**
 * Launch primary executable from configuration.
 *
 * @returns - the executable path object created.
 */
export function launchPrimaryExecutable(): ExecutablePath {
    const execObj = new ExecutablePath(
        getConfig("nukeExecutable.primaryExecutablePath") as string,
        "Main"
    );
    launchExecutable(execObj);
    return execObj;
}

/**
 * Launch secondary executable from configuration.
 *
 * @returns - the executable path object created.
 */
export function launchSecondaryExecutable(): ExecutablePath {
    const execObj = new ExecutablePath(
        getConfig("nukeExecutable.secondaryExecutablePath") as string,
        "Alt."
    );
    const defaultArgs = getConfig("nukeExecutable.options.defaultCommandLineArguments") as string;

    if (defaultArgs) {
        execObj.args = defaultArgs;
    }
    launchExecutable(execObj);
    return execObj;
}

/**
 * Launch main executable with prompt for optional arguments.
 *
 * @returns - the executable path object created.
 */
export async function launchPromptExecutable(): Promise<ExecutablePath> {
    const execObj = new ExecutablePath(
        getConfig("nukeExecutable.primaryExecutablePath") as string,
        "Main Prompt"
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
    return execObj;
}
