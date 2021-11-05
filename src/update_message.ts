import * as vscode from "vscode";

// This script is based on : https://stackoverflow.com/a/66307695/9392852

export class Version {
    version: number[];
    toStr: string;

    constructor(version: string | undefined) {
        if (version === undefined || version.indexOf(".") === -1) {
            version = "0.0.0";
        }
        this.toStr = version;
        this.version = version.split(".").map(Number);
    }

    major(): number {
        return this.version[0];
    }

    minor(): number {
        return this.version[1];
    }

    patch(): number {
        return this.version[2];
    }

    /**
     * Check if version is bigger than.
     *
     * Check happens only for minor and major but no patch. First will check if
     * minor version is bigger, if not will then check for major version.
     *
     * Examples:
     *  * 1.2.0 vs 1.1.0: true
     *  * 2.2.0 vs 1.1.0: true
     *  * 1.2.3 vs 1.2.0: false
     *
     * @param version - a Version object to check for version comparison.
     * @returns - true if yes, false otherwise
     */
    isBiggerThan(version: Version, includePatch: boolean): boolean {
        if (includePatch) {
            if (this.version > version.version) {
                return true;
            }
            return false;
        }

        if (this.minor() > version.minor() || this.major() > version.major()) {
            return true;
        }
        return false;
    }
}

// Show an update message if minor version is newer.
export function showUpdateMessage(context: vscode.ExtensionContext) {
    const extensionId = "virgilsisoe.nuke-tools";

    // get the value stored inside the global state for the key: _value['virgilsisoe.nuke-tools']
    // the first time there will be no value so it will return undefined.
    const previousVersion = new Version(
        context.globalState.get<string>(extensionId) as string
    );

    // get the package.json version
    const currentVersion = new Version(
        vscode.extensions.getExtension(extensionId)!.packageJSON
            .version as string
    );
    // TODO: stash git and find way to clean message
    // store the current version in the global state key _value['virgilsisoe.nuke-tools']
    context.globalState.update(extensionId, currentVersion.toStr);

    if (currentVersion.isBiggerThan(previousVersion, false)) {
        console.log("yes is bigger");
        const updateMsg = ``;

        if (updateMsg) {
            vscode.window.showInformationMessage(updateMsg);
        }
    }
}
