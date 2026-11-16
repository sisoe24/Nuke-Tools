import * as path from "path";

import * as vscode from "vscode";

import { PackageIds, Release, fetchLatestRelease, installZip, packageMap } from "./packages";

/**
 * Determine the configuration for extraPaths based on the current Python server.
 *
 *  - Pylance:  `python.analysis`
 *  - Jedi:  `python.autoComplete`
 *
 * @returns the settings name for the extra paths
 */
export function getPythonLspKey(): string {
    // when pythonServer is Default, we assume that Pylance is installed.
    const pythonServer = vscode.workspace.getConfiguration("python").get("languageServer");

    if (pythonServer === "Jedi") {
        return "python.autoComplete";
    }

    return "python.analysis";
}

/**
 * Get the stubs versions, newest first, from the release assets named `nuke-python-stubs-<version>.zip`.
 */
export function stubsAssets(release: Release): { version: string; url: string }[] {
    return release.assets
        .flatMap((asset) => {
            // the version becomes a folder name, so it must not contain a path
            const match = /^nuke-python-stubs-(\d[\w.]*)\.zip$/.exec(asset.name);
            return match ? [{ version: match[1], url: asset.browser_download_url }] : [];
        })
        .sort((a, b) => b.version.localeCompare(a.version, undefined, { numeric: true }));
}

/**
 * Return `extraPaths` with `stubsPath` as the only entry inside `stubsRoot`.
 *
 * Every other entry inside `stubsRoot`, `stubsRoot` itself included, is removed,
 * because the language server uses only the first `nuke` module it finds.
 */
export function replaceStubsPath(extraPaths: string[], stubsRoot: string, stubsPath: string): string[] {
    const isStubs = (p: string) => {
        const relative = path.relative(stubsRoot, p);
        return !relative.startsWith("..") && !path.isAbsolute(relative);
    };
    return [...extraPaths.filter((p) => !isStubs(p)), stubsPath];
}

/**
 * Set the stubs path in `extraPaths` of the workspace settings, or of the user
 * settings when no folder is open.
 */
async function updatePythonExtraPaths(stubsRoot: string, stubsPath: string) {
    const config = vscode.workspace.getConfiguration(getPythonLspKey(), null);
    const inspect = config.inspect<string[]>("extraPaths");

    const [target, current] = vscode.workspace.workspaceFolders
        ? // a workspace array replaces the user array, so start from the user entries
          [vscode.ConfigurationTarget.Workspace, inspect?.workspaceValue ?? inspect?.globalValue]
        : [vscode.ConfigurationTarget.Global, inspect?.globalValue];

    await config.update("extraPaths", replaceStubsPath(current ?? [], stubsRoot, stubsPath), target);
}

/**
 * Download the stubs of a Nuke version picked by the user and add them to `extraPaths`.
 */
export async function addStubs(): Promise<void> {
    if (!vscode.extensions.getExtension("ms-python.python")) {
        vscode.window.showErrorMessage(
            "Python extension is not installed. Could not add stubs path."
        );
        return;
    }

    const stubsRoot = packageMap.get(PackageIds.nukePythonStubs)!.destination;

    try {
        const assets = stubsAssets(await fetchLatestRelease(PackageIds.nukePythonStubs));
        if (!assets.length) {
            vscode.window.showErrorMessage("No Python stubs found in the latest release.");
            return;
        }

        const picked = await vscode.window.showQuickPick(
            assets.map((asset) => ({ label: asset.version, url: asset.url })),
            { placeHolder: "Nuke version of the stubs" }
        );
        if (!picked) {
            return;
        }

        const stubsPath = path.join(stubsRoot, picked.label);
        await installZip(picked.url, stubsPath);
        await updatePythonExtraPaths(stubsRoot, stubsPath);

        vscode.window.showInformationMessage(`Python stubs added for Nuke ${picked.label}.`);
    } catch (err) {
        vscode.window.showErrorMessage(`Could not add Python stubs: ${(err as Error).message}`);
    }
}
