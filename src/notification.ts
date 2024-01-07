import * as vscode from "vscode";

const _msg = `
VimDcc is now part of NukeTools. A Vim-like experience for Nuke's default Script Editor. Use the command \`NukeTools: Add VimDcc\` to install it.
More information on the official github (github.com/sisoe24/vimdcc) page.
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
