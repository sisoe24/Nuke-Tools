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
            destination: NUKE_TOOLS_DIR,
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
            destination: NUKE_TOOLS_DIR,
        },
    ],
]);

/**
 * Extract a zip file to a destination.
 *
 * @param source Source zip file.
 * @param destination Destination folder.
 */
function extractPackage(source: string, destination: string): void {
    destination += "-master";

    console.log(`NukeTools: Extracting package: ${source} to ${destination}`);

    try {
        extract(source, {
            dir: destination,
        })
            .then(() => {
                fs.rmSync(destination, { recursive: true });
                fs.renameSync(destination + "-master", destination);
                vscode.window.showInformationMessage(`NukeTools: Package updated: ${source}`);
            })
            .catch((err) => {
                vscode.window.showErrorMessage(
                    `NukeTools: Failed to extract package: ${source}. ${err}`
                );
            });
    } catch (err) {
        vscode.window.showErrorMessage(err as string);
        false;
    }
}

export function addPackage(packageId: PackageIds): PackageType {
    // const {currentVersion, previousVersion} = new Version();
    const pkg = packageMap.get(packageId);
    if (!pkg) {
        throw new Error(`Package ${packageId} not found`);
    }

    const archivedPackage = path.join(assets.ASSETS_PATH, `${pkg.name}.zip`);
    console.log(`NukeTools: Downloading package: ${pkg.name}, ${pkg.destination}`);
    // return

    if (fs.existsSync(archivedPackage) && Version.currentVersion <= Version.previousVersion) {
        console.log("NukeTools: Package already downloaded");
        extractPackage(archivedPackage, pkg.destination);
        return pkg;
    }

    const filterRelease = (release: GithubRelease) => {
        return release.prerelease === false;
    };

    downloadRelease("sisoe24", packageId, assets.ASSETS_PATH, filterRelease, undefined, true)
        .then(function () {
            extractPackage(archivedPackage, pkg.destination);
        })
        .catch(function (err: { message: unknown }) {
            console.error("NukeTools: Failed to download package from GitHub: ", err.message);
        });

    return pkg;
}
