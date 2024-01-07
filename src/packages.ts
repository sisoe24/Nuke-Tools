import * as fs from "fs";
import * as path from "path";

import * as vscode from "vscode";
import extract = require("extract-zip");
import { GithubRelease } from "@terascope/fetch-github-release/dist/src/interfaces";
import { downloadRelease } from "@terascope/fetch-github-release";

import * as assets from "./assets";
import * as nuke from "./nuke";
import { Version } from "./version";

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

const packageMap = new Map<PackageIds, PackageType>([
    [
        PackageIds.nukeServerSocket,
        {
            name: "NukeServerSocket",
            destination: nuke.nukeToolsDir,
        },
    ],
    [
        PackageIds.nukePythonStubs,
        {
            name: "nuke-python-stubs",
            destination: nuke.pythonStubsDir,
        },
    ],
    [
        PackageIds.pySide2Template,
        {
            name: "pyside2-template",
            destination: assets.ASSETS_PATH,
        },
    ],
    [
        PackageIds.vimdcc,
        {
            name: "vimdcc",
            destination: nuke.nukeToolsDir,
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
    try {
        extract(source, {
            dir: destination,
        })
            .then(() => {
                console.log(`NukeTools: Package updated: ${source}`);
            })
            .catch((err) => {
                console.log(err);
            });
    } catch (err) {
        vscode.window.showErrorMessage(err as string);
        false;
    }
}

export function getPackage(packageId: PackageIds): void {

    const {currentVersion, previousVersion} = new Version();

    const archivedPackage = path.join(assets.ASSETS_PATH, `${packageId}.zip`);
    const pkg = packageMap.get(packageId);
    if (!pkg) {
        throw new Error(`Package ${packageId} not found`);
    }

    if (fs.existsSync(archivedPackage) && currentVersion <= previousVersion) {
        console.log("NukeTools: Package already downloaded");
        extractPackage(archivedPackage, pkg.destination);
        return;
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
}
