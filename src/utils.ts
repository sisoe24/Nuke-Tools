import * as vscode from "vscode";

// Get configuration settings
export function getConfig(field: string): any {
    const config = vscode.workspace.getConfiguration(`nukeTools`);
    const subConfig = config.get(field);

    if (subConfig === undefined) {
        throw new Error(`Configuration: ${field} doesn't exist`);
    }

    return subConfig;
}
