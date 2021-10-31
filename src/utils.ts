import * as vscode from 'vscode';



// Get configuration settings
export function getConfiguration(field: string): string | boolean {
    const config = vscode.workspace.getConfiguration(`nukeTools`);
    const subConfig = config.get(field);

    if (subConfig === undefined) {
        console.error(`configuration: ${field} doesn't exist`);
        return false;
    }

    config.update('nukeExecutable.primaryExecutablePath', undefined);
    return subConfig as boolean | string;
}


function getStubsPath() {
    const currentPath = vscode.extensions.getExtension('virgilsisoe.nuke-tools')!.extensionPath;
    return require('path').join(currentPath, 'Nuke-Python-Stubs', 'nuke_stubs');

}

/**
 * Add stubs folder path to workspace settings `python.analysis.extraPaths`.
 * If path is already present, do nothing.
 */
export function addStubsPath() {

    const stubsPath = getStubsPath();

    const config = vscode.workspace.getConfiguration('python.analysis');
    let extraPaths = config.get('extraPaths') as Array<string>;

    if (!extraPaths.includes(stubsPath)) {
        extraPaths.push(stubsPath);
        config.update('extraPaths', extraPaths);
    }
}