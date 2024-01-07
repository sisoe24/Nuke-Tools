import * as vscode from "vscode";

export class Version {

    private static previousVersion: string;
    private static currentVersion: string;

    public get previousVersion(): string {
        return Version.previousVersion;
    }

    public get currentVersion(): string {
        return Version.currentVersion;
    }

    public static update(cxt: vscode.ExtensionContext): void {
        Version.previousVersion = (cxt.globalState.get(cxt.extension.id + ".version") as string) || "0.0.0";
        Version.currentVersion = cxt.extension.packageJSON.version;
    }
}
