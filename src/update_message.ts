import * as vscode from 'vscode';

// This script is based on : https://stackoverflow.com/a/66307695/9392852

// Check for the current and previous version
function isNewVersion(previousVersion: string, currentVersion: string) {

    // if string doesn't contain a dot
    if (previousVersion.indexOf(".") === -1) {
        return true;
    }

    // returns int array [1,1,1] i.e. [major, minor, patch]
    let previousVerArr = previousVersion.split(".").map(Number);
    let currentVerArr = currentVersion.split(".").map(Number);

    // check by minor update
    if (currentVerArr[1] > previousVerArr[1]) {
        return true;
    }

    return false;
}

// Show an update message if minor version is newer.
export async function showUpdateMessage(context: vscode.ExtensionContext) {
    const extensionId = 'virgilsisoe.nuke-tools';

    // get the variable version stored inside the global state. will be undefined first time
    const previousVersion = context.globalState.get<string>(extensionId);

    // get the package.json version
    const currentVersion = vscode.extensions.getExtension(extensionId)!.packageJSON.version;

    // store the current version in a global state variable.
    context.globalState.update(extensionId, currentVersion);

    if (previousVersion === undefined || isNewVersion(previousVersion, currentVersion)) {

        // leave an empty string if update doesn't need a message
        const updateMsg = `Stubs file included with extension. Check more on README`;

        if (updateMsg) {
            const actions = [{ title: "See how" }];
            const result = await vscode.window.showInformationMessage(updateMsg);
        }

    }
}