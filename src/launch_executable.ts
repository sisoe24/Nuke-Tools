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
        this.execPath = execPath;
        this.terminalSuffix = terminalSuffix;

        this.args = "";
    }

    /**
     * Create the terminal name based on path basename and terminalSuffix argument.
     *
     * @returns the terminal name.
     */
    terminalName(): string {
        return `${path.basename(this.execPath)} ${this.terminalSuffix}`;
    }

    /**
     * Check if path exists. If not, will show an error message to user.
     *
     * @returns - True if does, False otherwise
     */
    exists(): boolean {
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
        return `${this.execPath} ${this.args}`.trim();
    }
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

    let env = getConfig("other.envVars") as EnvVars;

    if (getConfig("other.useSystemEnvVars") as boolean) {
        env = concatEnv(env);
    }

    return `${stringifyEnv(env)} ${cliCmd}`;
}

/**
 * Execute the command in the terminal. Before executing the command, if restartInstance
 * is enabled, will dispose of the previous terminal instance.
 *
 * @param execPath - ExecutablePath object.
 */
export function execCommand(execPath: ExecutablePath): void {
    const terminalName = execPath.terminalName();

    if (getConfig("nukeExecutable.options.restartInstance")) {
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name === terminalName) {
                terminal.dispose();
            }
        });
    }

    const terminal = vscode.window.createTerminal(terminalName);

    terminal.sendText(getCliCmd(execPath));
    terminal.show(true);
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

    if (execObj.exists()) {
        execCommand(execObj);
    }

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

    if (execObj.exists()) {
        execCommand(execObj);
    }

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

    if (execObj.exists()) {
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
