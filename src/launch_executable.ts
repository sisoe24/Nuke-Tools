import * as os from "os";
import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

import { getConfig, EnvVars, ExecutableConfig } from "./config";
const IS_WINDOWS = os.type() === "Windows_NT";

const isPowerShell = () => {
    const { shell } = vscode.env;
    if (shell.includes("powershell") || shell.includes("pwsh")) {
        return true;
    }
    return false;
};

const isUnixShell = () => {
    const { shell } = vscode.env;
    if (!isPowerShell() && !shell.includes("cmd")) {
        return true;
    }
    return false;
};

/**
 * ExecutablePath object class.
 */
export class ExecutablePath {
    name: string;
    path: string;
    args: string;

    /**
     * Init method for the ExecutablePath object.
     *
     * @param name - The name of the executable.
     * @param path - The path for the executable file.
     * @param args - Optional arguments for the command line
     */
    constructor(name: string, path: string, args = "") {
        this.name = name;
        this.path = path;
        this.args = args;
    }

    /**
     * Check if path exists. If not, will show an error message to user.
     *
     * @returns - True if does, False otherwise
     */
    exists(): boolean {
        if (!fs.existsSync(this.path)) {
            vscode.window.showErrorMessage(`Cannot find path: ${this.path}.`);
            return false;
        }
        return true;
    }

    /**
     *  Create the cli command to be executed inside the terminal.
     *
     * @returns  - string like command for the terminal.
     */
    buildExecutableCommand(): string {
        let cmd = `"${this.path}" ${this.args}`;

        if (isPowerShell()) {
            cmd = `& ${cmd}`;
        }

        return cmd.trim();
    }
}

/**
 * Concatenate the user's environment variables with the system's environment variables.
 *
 * @param userEnvironmentVars EnvVars object containing the user's environment variables
 * return an EnvVars object containing the concatenated environment variables
 */
function concatEnv(userEnvironmentVars: EnvVars): EnvVars {
    const env: EnvVars = {};

    let workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath || "";

    // on windows we need to convert the path to a unix-like path
    if (IS_WINDOWS && isUnixShell()) {
        workspaceFolder = workspaceFolder.replace(/\\/g, "/");
        workspaceFolder = workspaceFolder.replace(/^([a-zA-Z]):/, (_, driveLetter) => {
            return `/${driveLetter.toLowerCase()}`;
        });
    }

    for (const [k, v] of Object.entries(userEnvironmentVars)) {
        // Replace all instances of $envVar with the system environment variable
        env[k] = v.replace(new RegExp(`\\$${k}`, "g"), process.env[k] || "");

        // Replace all instances of ${workspaceFolder} with the workspace folder path
        env[k] = env[k].replace(/\${workspaceFolder}/g, workspaceFolder);

        // Clean up the path separator in the beginning and end of the string
        env[k] = env[k].replace(/^[\s:;]+|[\s:;]+$/g, "");
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
        if (isPowerShell()) {
            envString += `$env:${k}="${v}"; `;
        } else if (isUnixShell()) {
            envString += `${k}=${v} `;
        } else {
            // cmd
            envString += `set ${k}=${v}&&`;
        }
    }

    return envString;
}

/**
 * Execute the command in the terminal. Before executing the command, if restartInstance
 * is enabled, will dispose of the previous terminal instance.
 *
 * @param execPath - ExecutablePath object.
 */
export function execCommand(execPath: ExecutablePath): void {
    const terminalName = `${path.basename(execPath.path)} ${execPath.name}`;

    if (getConfig("nukeExecutable.restartInstance")) {
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name === terminalName) {
                terminal.dispose();
            }
        });
    }

    const env = stringifyEnv(concatEnv(getConfig("nukeExecutable.envVars")));
    const command = `${env} ${execPath.buildExecutableCommand()}`.trim();

    const terminal = vscode.window.createTerminal(terminalName);
    terminal.sendText(command);
    terminal.show(true);
}

/**
 * Launch primary executable from configuration.
 *
 * @returns - the executable path object created.
 */
export function launchPrimaryExecutable(): ExecutablePath {
    const execObj = new ExecutablePath(
        "Main",
        getConfig("nukeExecutable.primaryExecutablePath"),
        getConfig("nukeExecutable.commandLineArguments")
    );

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
        "Main Prompt",
        getConfig("nukeExecutable.primaryExecutablePath")
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

export function launchExecutable(name: string, executableConfig: ExecutableConfig): void {
    const execObj = new ExecutablePath(name, executableConfig.bin, executableConfig.args);

    if (execObj.exists()) {
        execCommand(execObj);
    }
}
