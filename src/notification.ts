import * as vscode from "vscode";

const _msg = `
NukeServerSocket has been updated to version 1.0.0. There are some breaking changes in the API.
If you encounter any issues, please open an issue on GitHub. Sorry for the inconvenience.
`;

/**
 * Show update message box if version is newer or update message is different.
 *
 * @param context vscode ExtensionContext
 */
export function showNotification(context: vscode.ExtensionContext, msg: string = _msg): void {
    const extensionId = context.extension.id;

    // get the value stored inside the global state key: _value['extension.version']
    const extVersion = extensionId + ".version";
    const previousVersion = context.globalState.get(extVersion) as string;

    // update the value stored inside the global state key: _value['extension.updateMsg']
    const extUpdateMsg = extensionId + ".updateMsg";
    const previousMsg = context.globalState.get(extUpdateMsg) as string;
    context.globalState.update(extUpdateMsg, msg);

    // get the package.json version and store in the global state key _value['extensionId.version']
    const currentVersion = context.extension.packageJSON.version;
    context.globalState.update(extVersion, currentVersion);

    if (currentVersion > previousVersion && msg !== previousMsg) {
        vscode.window.showInformationMessage(msg);
    }
}
