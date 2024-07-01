import * as vscode from "vscode";

export type ExecutableConfig = {
    bin: string;
    args: string;
};

type ExecutableMap = {
    [key: string]: ExecutableConfig;
};

export type EnvVars = { [key: string]: string };

type Executables = "nukeExecutable.executables";

type StringConfig =
    | "pythonPath"
    | "pythonStubsPath"
    | "nukeExecutable.commandLineArguments"
    | "nukeExecutable.secondaryExecutablePath"
    | "nukeExecutable.primaryExecutablePath";

type ObjectConfig = "nukeExecutable.envVars";

type BooleanConfig =
    | "nukeExecutable.restartInstance"
    | "network.enableManualConnection"
    | "other.clearPreviousOutput"
    | "network.debug";

export type ManualConnection = {
    active: boolean;
    host: string;
    port: string;
};

type ManualConnectionConfig = "network.manualConnection";

type ConfigProperty =
    | StringConfig
    | BooleanConfig
    | Executables
    | ObjectConfig
    | ManualConnectionConfig;

/**
 * Get a configuration property.
 *
 * This is a wrapper around vscode.workspace.getConfiguration to avoid having some
 * boilerplate code. It calls the root configuration and then get the property.
 *
 * @param property - name of the configuration property to get.
 * @returns - the value of the property.
 * @throws Error if the property doesn't exist.
 */
export function getConfig(property: ObjectConfig): EnvVars;
export function getConfig(property: BooleanConfig): boolean;
export function getConfig(property: StringConfig): string;
export function getConfig(property: Executables): ExecutableMap;
export function getConfig(property: ManualConnectionConfig): ManualConnection;
export function getConfig(property: ConfigProperty): unknown {
    const config = vscode.workspace.getConfiguration("nukeTools");
    const subConfig = config.get(property);

    if (typeof subConfig === "undefined") {
        throw new Error(`Configuration: ${property} doesn't exist`);
    }

    return subConfig;
}
