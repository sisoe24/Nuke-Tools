import * as fs from "fs";
import * as path from "path";
import * as os from "os";

import * as vscode from "vscode";
import extract = require("extract-zip");
import { GithubRelease } from "@terascope/fetch-github-release/dist/src/interfaces";
import { downloadRelease } from "@terascope/fetch-github-release";

import * as assets from "./assets";
import { Version } from "./version";

const NUKE_TOOLS_DIR = path.join(os.homedir(), ".nuke", "NukeTools");

type PackageType = {
    name: string;
    destination: string;
};

export enum PackageIds {
    nukeServerSocket = "NukeServerSocket",
    nukePythonStubs = "nuke-python-stubs",
    pySide2Template = "pyside2-template",
    vimdcc = "vimdcc",
}

export const packageMap = new Map<PackageIds, PackageType>([
    [
        PackageIds.nukeServerSocket,
        {
            name: "NukeServerSocket",
            destination: path.join(NUKE_TOOLS_DIR, "NukeServerSocket"),
        },
    ],
    [
        PackageIds.nukePythonStubs,
        {
            name: "nuke-python-stubs",
            destination: path.join(NUKE_TOOLS_DIR, "stubs"),
        },
    ],
    [
        PackageIds.pySide2Template,
        {
            name: "pyside2-template",
            destination: NUKE_TOOLS_DIR,
        },
    ],
    [
        PackageIds.vimdcc,
        {
            name: "vimdcc",
            destination: path.join(NUKE_TOOLS_DIR, "vimdcc"),
        },
    ],
]);

/**
 * Extract a zip file to a destination.
 *
 * Because the zip file will completely replace the destination folder,
 * the destination folder will be renamed to destination + "-master"
 * to prevent the destination folder from being replaced if something goes wrong during the extraction.
 *
 * @param source Source zip file.
 * @param destination Destination folder.
 */
function extractPackage(source: string, destination: string): Promise<void> {
    return new Promise((resolve, reject) => {
        try {
            extract(source, { dir: destination + "-master" })
                .then(() => {
                    if (fs.existsSync(destination)) {
                        fs.rmSync(destination, { recursive: true });
                    }
                    fs.renameSync(destination + "-master", destination);
                    vscode.window.showInformationMessage(`NukeTools: Package updated: ${source}`);
                    resolve();
                })
                .catch((err) => {
                    vscode.window.showErrorMessage(
                        `NukeTools: Failed to extract package: ${source}. ${err}`
                    );
                    reject(err);
                });
        } catch (err) {
            vscode.window.showErrorMessage(err as string);
            reject(err);
        }
    });
}

/**
 * Add a package to the .nuke/NukeTools folder.
 *
 * Adding a package can be done in two ways:
 *  - Download the latest release from GitHub
 *  - Extract the package from the assets folder
 *
 * When the package is downloaded from GitHub, it will be extracted to the assets folder.
 * So the next time the package is added, it will be extracted from the assets folder.
 *
 * @param packageId the package to add
 * @returns
 */
export async function addPackage(
    packageId: PackageIds,
    force = false
): Promise<PackageType | null> {
    const pkg = packageMap.get(packageId);
    if (!pkg) {
        throw new Error(`Package ${packageId} not found`);
    }

    const archivedPackage = path.join(assets.ASSETS_PATH, `${pkg.name}.zip`);

    if (
        !force &&
        fs.existsSync(archivedPackage) &&
        Version.currentVersion <= Version.previousVersion
    ) {
        await extractPackage(archivedPackage, pkg.destination);
        return pkg;
    }

    const filterRelease = (release: GithubRelease) => {
        return release.prerelease === false;
    };

    return downloadRelease("sisoe24", packageId, assets.ASSETS_PATH, filterRelease, undefined, true)
        .then(async function () {
            await extractPackage(archivedPackage, pkg.destination);
            return pkg;
        })
        .catch(function (err: { message: unknown }) {
            vscode.window.showWarningMessage(
                "NukeTools: Failed to download package from GitHub: " + err.message
            );
            return null;
        });
}

export async function forceUpdatePackages(): Promise<void> {
    for (const [packageId, pkg] of packageMap) {
        await addPackage(packageId, true);
    }
}
