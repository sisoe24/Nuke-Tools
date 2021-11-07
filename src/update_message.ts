import * as vscode from "vscode";

// This script is based on: https://stackoverflow.com/a/66307695/9392852

/**
 * Show update message box if version is newer or update message is different.
 *
 * @param context vscode ExtensionContext
 */
export function showUpdateMessage(context: vscode.ExtensionContext): void {
    const extensionId = "virgilsisoe.nuke-tools";

    // get the value stored inside the global state key: _value['virgilsisoe.nuke-tools.version']
    const extVersion = extensionId + ".version";
    const previousVersion = context.globalState.get<string>(extVersion) as string;

    // get the value stored inside the global key: _value['virgilsisoe.nuke-tools.updateMsg']
    const extUpdateMsg = extensionId + ".updateMsg";
    const previousMsg = context.globalState.get<string>(extUpdateMsg) as string;

    // get the package.json version
    const currentVersion = vscode.extensions.getExtension(extensionId)!.packageJSON
        .version as string;

    // store the current version in the global state key _value['virgilsisoe.nuke-tools.version']
    context.globalState.update(extVersion, currentVersion);

    const updateMsg = "";

    // store the current update message in the global state key _value['virgilsisoe.nuke-tools.updateMsg']
    context.globalState.update(extUpdateMsg, updateMsg);

    if (currentVersion > previousVersion && updateMsg !== previousMsg) {
        vscode.window.showInformationMessage(updateMsg);
    }
}
