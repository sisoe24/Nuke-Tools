import * as vscode from "vscode";
import * as fs from "fs";
import { ASSETS_LOG_PATH } from "./constants";

export class Version {
    private static _extPreviousVersion: string;
    private static _extCurrentVersion: string;

    /**
     * Get the previous version of the extension.
     */
    public static get extPreviousVersion(): string {
        return Version._extPreviousVersion;
    }

    /**
     * Get the current version of the extension.
     */
    public static get extCurrentVersion(): string {
        return Version._extCurrentVersion;
    }

    public static update(cxt: vscode.ExtensionContext): void {
        Version._extPreviousVersion =
            (cxt.globalState.get(cxt.extension.id + ".version") as string) || "0.0.0";
        Version._extCurrentVersion = cxt.extension.packageJSON.version;
    }

    public static getPackageVersion(packageName: string): string {
        const logFile = fs.readFileSync(ASSETS_LOG_PATH, "utf8");
        const data = JSON.parse(logFile);
        return data["packages"][packageName];
    }
}
