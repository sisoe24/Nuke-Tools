import * as vscode from "vscode";

import { isNewerVersion } from "./packages";

const _msg = `
0.18.0. Removed the PySide2 template and VimDCC packages. Check the changelog for more details.
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

    if (previousVersion && isNewerVersion(currentVersion, previousVersion) && msg !== previousMsg) {
        vscode.window.showInformationMessage(msg);
    }
}
