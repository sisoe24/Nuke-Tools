import * as vscode from 'vscode';

export function validatePath(path: string): string {

    // TODO: should also check if file is executable?
    // require('fs').statSync(cmd).mode will return a value that kind of helps

    if (!require('fs').existsSync(path)) {
        console.log('file path does not exist');
        vscode.window.showErrorMessage(`Cannot find path: ${path}.`);
        return '';
    }

    // if path has spaces then will break
    path = `"${path}"`;

    // on windows if path has spaces needs the & so just in case
    if (require('os').type() === 'Windows_NT') {
        path = `& ${path}`;
    }

    return path;
}

export function getExecutable(exec: string): string {
    const execPath = getConfiguration(`nukeExecutable.${exec}`);
    const path = validatePath(execPath);
    if (path) { return path; };
    return '';
}

export function getConfiguration(field: string): string {
    const config = vscode.workspace.getConfiguration(`nukeTools`);
    const subConfig = config.get(field);

    if (subConfig === undefined) {
        console.error(`configuration: ${field} doesn't exist`);
        return '';
    }

    return subConfig as string;
}
