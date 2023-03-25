import * as vscode from "vscode";
import * as path from "path";
import * as os from "os";

import * as utils from "./utils";

import { GithubRelease } from "@terascope/fetch-github-release/dist/src/interfaces";
import { downloadRelease } from "@terascope/fetch-github-release";

import extract = require("extract-zip");

/**
 * Download a package from the github release page.
 */
function downloadPackage(repo: string, destination: string) {
    function filterRelease(release: GithubRelease) {
        return release.prerelease === false;
    }

    downloadRelease("sisoe24", repo, destination, filterRelease, undefined)
        .then(function () {
            console.log(`Package updated: ${repo}`);
        })
        .catch(async function (err: { message: any }) {
            try {
                await extract(utils.getIncludedPath("include", `${repo}.zip`), {
                    dir: path.join(utils.extensionPath(), "assets"),
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
 */
export function updatePackage(
    context: vscode.ExtensionContext,
    packageId: string,
    currentVersion: string
) {
    const pkgVersionId = `virgilsisoe.nuke-tools.${packageId}`;

    // just be sure I dont ship the code since I need to reset the version for testing purposes
    if (os.userInfo()["username"] === "virgilsisoe") {
        context.globalState.update(pkgVersionId, "0.0.0");
    }

    const previousPkgVersion = (context.globalState.get(pkgVersionId) as string) ?? "0.0.0";

    if (currentVersion > previousPkgVersion) {
        console.log("should update package");

        if (downloadPackage(packageId, path.join(utils.extensionPath(), "assets", packageId))) {
            context.globalState.update(pkgVersionId, currentVersion);
        }
    }
}
