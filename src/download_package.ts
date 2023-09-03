import * as path from "path";
import * as utils from "./utils";
import * as vscode from "vscode";

import { existsSync, mkdirSync } from "fs";

import extract = require("extract-zip");

import { GithubRelease } from "@terascope/fetch-github-release/dist/src/interfaces";
import { downloadRelease } from "@terascope/fetch-github-release";


const assetsPath = path.join(utils.extensionPath(), "assets");
if (!existsSync(assetsPath)) {
    mkdirSync(assetsPath);
}

/**
 * nuke-python-stubs are only the stubs from the repo
 * pyside2-template is the source code: git archive ...
 * NukeServerSocket is the source code
 */
const PACKAGES = {
    NukeServerSocket: "0.6.0",
    "nuke-python-stubs": "0.2.3",
    "pyside2-template": "0.2.0",
};

/**
 * Download a package from the github release page.
 */
function downloadPackage(repo: string, destination: string) {
    function filterRelease(release: GithubRelease) {
        return release.prerelease === false;
    }

    downloadRelease("sisoe24", repo, destination, filterRelease)
        .then(function () {
            console.log(`Package updated: ${repo}`);
        })
        .catch(async function (err: { message: any }) {
            vscode.window.showWarningMessage(
                `Failed to download package from GitHub: ${err}. Fallback on local zip.`
            );
            try {
                await extract(utils.getIncludePath(`${repo}.zip`), {
                    dir: path.join(utils.extensionPath(), "assets", repo),
                });
            } catch (err) {
                vscode.window.showErrorMessage(err as string);
                return false;
            }
        });

    return true;
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
    packageId: string,
    currentVersion: string
): void {
    const pkgVersionId = `virgilsisoe.nuke-tools.${packageId}`;
    const previousPkgVersion = (context.globalState.get(pkgVersionId) as string) ?? "0.0.0";

    if (
        currentVersion > previousPkgVersion &&
        downloadPackage(packageId, path.join(assetsPath, packageId))
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
    for (const [pkg, version] of Object.entries(PACKAGES)) {
        if (forceUpdate) {
            context.globalState.update(`virgilsisoe.nuke-tools.${pkg}`, "0.0.0");
        }
        updatePackage(context, pkg, version);
    }
}
