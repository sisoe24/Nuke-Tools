import * as path from "path";
import * as assets from "./assets";
import * as vscode from "vscode";

import extract = require("extract-zip");

import { GithubRelease } from "@terascope/fetch-github-release/dist/src/interfaces";
import { downloadRelease } from "@terascope/fetch-github-release";

export enum Package {
    nukeServerSocket = "NukeServerSocket",
    nukePythonStubs = "nuke-python-stubs",
    pySide2Template = "pyside2-template",
    vimdcc = "vimdcc",
}

// TODO: Get latest version from github api
const latest = new Map<Package, string>([
    [Package.nukeServerSocket, "0.6.2"],
    [Package.nukePythonStubs, "0.2.4"],
    [Package.pySide2Template, "0.2.0"],
    [Package.vimdcc, "0.1.0"]
]);

/**
 * Download a package from the github release page. If the download fails, 
 * fallback on the local zip.
 * 
 * @param repo A {@link Package} name
 * @param destination Destination path
 * @returns true if the package was downloaded, false otherwise.
 */
function downloadPackage(repo: Package, destination: string): boolean {
    function filterRelease(release: GithubRelease) {
        return release.prerelease === false;
    }

    downloadRelease("sisoe24", repo, destination, filterRelease)
        .then(function () {
            console.log(`Package updated: ${repo}`);
        })
        .catch(async function (err: { message: unknown }) {
            vscode.window.showWarningMessage(
                `Failed to download package from GitHub: ${err.message}. Fallback on local zip.`
            );
            try {
                await extract(assets.getPath("include", `${repo}.zip`), {
                    dir: path.join(assets.PATH, repo),
                });
            } catch (err) {
                vscode.window.showErrorMessage(err as string);
                return false;
            }
        });

    return true;
}

/**
 * Utility function to download the Stubs package.
 *
 * @param dest Destination path
 * @returns true if the package was downloaded, false otherwise.
 */
export function downloadStubs(dest: string): boolean {
    return downloadPackage(Package.nukePythonStubs, dest);
}

/**
 * Update a package if a newer version is released.
 *
 * @param context vscode.ExtensionContext
 * @param packageId Package name
 * @param currentVersion Current version of the package
 *
 */
export function updatePackage(
    context: vscode.ExtensionContext,
    packageId: Package,
    currentVersion: string
): void {
    const pkgVersionId = `virgilsisoe.nuke-tools.${packageId}`;
    const previousPkgVersion = (context.globalState.get(pkgVersionId) as string) ?? "0.0.0";

    if (
        currentVersion > previousPkgVersion &&
        downloadPackage(packageId, path.join(assets.PATH, packageId))
    ) {
        context.globalState.update(pkgVersionId, currentVersion);
    }
}

/**
 * Check if a package needs to be updated. If so, update it.
 *
 * @param context vscode.ExtensionContext
 * @param forceUpdate Force update all packages
 */
export function checkPackageUpdates(context: vscode.ExtensionContext, forceUpdate = false): void {
    for (const [pkg, version] of latest) {
        if (forceUpdate) {
            context.globalState.update(`virgilsisoe.nuke-tools.${pkg}`, "0.0.0");
        }
        updatePackage(context, pkg, version);
    }
}
