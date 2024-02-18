import * as vscode from "vscode";

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
export function getConfig(property: string): unknown {
    const config = vscode.workspace.getConfiguration("nukeTools");
    const subConfig = config.get(property);

    if (typeof subConfig === "undefined") {
        throw new Error(`Configuration: ${property} doesn't exist`);
    }

    return subConfig;
}
