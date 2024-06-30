import * as vscode from "vscode";

export type ExecutableConfig = {
    path: string;
    commandArgs: string;
};

type ExecutableMap = {
    [key: string]: ExecutableConfig;
};

export type EnvVars = { [key: string]: string };
type Executables = "executables";
type StringConfig =
    | "pythonPath"
    | "pythonStubsPath"
    | "nukeExecutable.options.defaultCommandLineArguments"
    | "nukeExecutable.secondaryExecutablePath"
    | "nukeExecutable.primaryExecutablePath";

type ObjectConfig = "other.envVars";
type BooleanConfig =
    | "nukeExecutable.options.restartInstance"
    | "other.useSystemEnvVars"
    | "network.enableManualConnection"
    | "other.clearPreviousOutput"
    | "network.debug";
type ConfigProperty = StringConfig | BooleanConfig | Executables | ObjectConfig;

/**
 * Get a configuration property.
 *
 * This is a wrapper around vscode.workspace.getConfiguration to avoid having some
 * boilerplate code. It calls the root configuration and then get the property.
 *
 * Example:
 * ```ts
 * const config = getConfig("console");
 * ```
 *
 * @param property - name of the configuration property to get.
 * @returns - the value of the property.
 * @throws Error if the property doesn't exist.
 */
export function getConfig(property: ObjectConfig): EnvVars;
export function getConfig(property: BooleanConfig): boolean;
export function getConfig(property: StringConfig): string;
export function getConfig(property: Executables): ExecutableMap;
export function getConfig(property: ConfigProperty): unknown {
    const config = vscode.workspace.getConfiguration("nukeTools");
    const subConfig = config.get(property);

    if (typeof subConfig === "undefined") {
        throw new Error(`Configuration: ${property} doesn't exist`);
    }

    return subConfig;
}
