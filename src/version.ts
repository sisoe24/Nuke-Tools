import * as vscode from "vscode";

export class Version {

    private static _previousVersion: string;
    private static _currentVersion: string;

    public static get previousVersion(): string {
        return Version._previousVersion;
    }

    public static get currentVersion(): string {
        return Version._currentVersion;
    }

    public static update(cxt: vscode.ExtensionContext): void {
        Version._previousVersion = (cxt.globalState.get(cxt.extension.id + ".version") as string) || "0.0.0";
        Version._currentVersion = cxt.extension.packageJSON.version;
    }
}
