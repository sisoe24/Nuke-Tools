import * as vscode from "vscode";

/**
 * Get configuration property value.
 *
 * If property name is not found, throws an error.
 *
 * @param property - name of the configuration property to get.
 * @returns - the value of the property.
 */
export function nukeToolsConfig(property: string): any {
    const config = vscode.workspace.getConfiguration(`nukeTools`);
    const subConfig = config.get(property);

    if (subConfig === undefined) {
        throw new Error(`Configuration: ${property} doesn't exist`);
    }

    return subConfig;
}
