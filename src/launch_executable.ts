import * as os from "os";
import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

import { getConfig, EnvVars, ExecutableConfig } from "./config";
const IS_WINDOWS = os.type() === "Windows_NT";

const isPowerShell = () => {
    const { shell } = vscode.env;
    return shell.includes("powershell") || shell.includes("pwsh");
};

const isCmdShell = () => {
    return vscode.env.shell.includes("cmd");
};

const isUnixShell = () => {
    return !isPowerShell() && !isCmdShell();
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
 * Replace placeholders in a string with their corresponding values.
 * 
 * @example
 * resolveEnvVariables("foo ${workspaceFolder} $SHELL bar");
 * // => "foo /home/user /bin/bash bar"
 *
 * @param text - The text to resolve the placeholders in.
 * @return - The text with the placeholders resolved.
 */
function resolveEnvVariables(text: string):string {
    let workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath || "";

    // on windows we need to convert the path to a unix-like path
    if (IS_WINDOWS && isUnixShell()) {
        workspaceFolder = workspaceFolder.replace(/\\/g, "/");
        // Convert the drive letter to lowercase and add a leading slash (e.g. C: -> /c)
        workspaceFolder = workspaceFolder.replace(/^([a-zA-Z]):/, (_, driveLetter) => {
            return `/${driveLetter.toLowerCase()}`;
        });
    }

    const placeholders: { [key: string]: string } = {
        workspaceFolder: workspaceFolder,
        workspaceFolderBasename: path.basename(workspaceFolder),
        userHome: os.homedir(),
    };

    for (const [placeholder, replacement] of Object.entries(placeholders)) {
        text = text.replace(new RegExp(`\\$\\{${placeholder}\\}`, "g"), replacement);
    }

    for (const match of text.match(/\$\w+/g) || []) {
        text = text.replace(match, process.env[match.replace("$", "")] || match);
    }

    return text;
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
        const envPath = v.join(path.delimiter);
        if (isPowerShell()) {
            envString += `$env:${k}="${envPath}"; `;
        } else if (isUnixShell()) {
            envString += `${k}=${envPath} `;
        } else if (isCmdShell()) {
            envString += `set ${k}=${envPath}&&`;
        } else {
            envString += `${k}=${envPath} `;
            vscode.window.showWarningMessage(
                `Unknown shell detected ${vscode.env.shell}. Environment variables may not be set correctly.`
            );
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
function execCommand(execPath: ExecutablePath): void {
    const terminalName = `${path.basename(execPath.path)} ${execPath.name}`;

    if (getConfig("restartTerminalInstance")) {
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name === terminalName) {
                terminal.dispose();
            }
        });
    }

    const env = stringifyEnv(getConfig("environmentVariables"));
    console.log(env);
    const command = resolveEnvVariables(`${env} ${execPath.buildExecutableCommand()}`.trim());
    console.log(command);
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
        getConfig("executablePath"),
        getConfig("executableArgs")
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
    const execObj = new ExecutablePath("Main Prompt", getConfig("executablePath"));

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
