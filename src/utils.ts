import * as vscode from 'vscode';

export function getConfiguration(field: string): string {
    const config = vscode.workspace.getConfiguration(`nukeTools`);
    const subConfig = config.get(field);

    if (subConfig === undefined) {
        console.error(`configuration: ${field} doesn't exist`);
        return '';
    }

    return subConfig as string;
}
