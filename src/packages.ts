import * as fs from "fs";
import * as path from "path";

import * as vscode from "vscode";
import extract = require("extract-zip");
import { GithubRelease } from "@terascope/fetch-github-release/dist/src/interfaces";
import { downloadRelease } from "@terascope/fetch-github-release";

import { Version } from "./version";
import { NUKE_TOOLS_DIR, ASSETS_PATH } from "./constants";


type PackageType = {
    name: string;
    destination: string;
};

export enum PackageIds {
    nukeServerSocket = "nukeserversocket",
    nukePythonStubs = "nuke-python-stubs",
    pySide2Template = "pyside2-template",
    vimdcc = "vimdcc",
}

export const packageMap = new Map<PackageIds, PackageType>([
    [
        PackageIds.nukeServerSocket,
        {
            name: "nukeserversocket",
            destination: path.join(NUKE_TOOLS_DIR, "nukeserversocket"),
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

function shouldUpdate(packageName: string): boolean {
    if (Version.extCurrentVersion > Version.extPreviousVersion) {
        return true;
    }

    const expectedPackageVersion = Version.getPackageVersion(packageName);

    const currentPackageVersion = "v0.0.0";

    if (expectedPackageVersion > currentPackageVersion) {
        return true;
    }

    return false;
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
 * If the package is already in the assets folder and the current version is not greater than the previous version,
 * the package will be extracted from the assets folder.
 *
 * @param packageId the package to add
 * @param destination the destination folder. If not provided, the package's default destination will be used.
 * @ param force if true, the package will be downloaded from GitHub, even if it already exists in the assets folder.
 * @returns
 */
export async function addPackage(
    packageId: PackageIds,
    destination?: string
): Promise<PackageType | null> {
    const pkg = packageMap.get(packageId);

    if (!pkg) {
        throw new Error(`Package ${packageId} not found`);
    }

    if (!destination) {
        destination = pkg.destination;
    }

    const archivedPackage = path.join(ASSETS_PATH, `${pkg.name}.zip`);

    // every new version the package will be downloaded from GitHub
    if (fs.existsSync(archivedPackage) && !shouldUpdate(pkg.name)) {
        await extractPackage(archivedPackage, destination);
        vscode.window.showInformationMessage(`NukeTools: Package added: ${pkg.name}`);
        return pkg;
    }

    const filterRelease = (release: GithubRelease) => {
        return release.prerelease === false;
    };

    return downloadRelease("sisoe24", packageId, ASSETS_PATH, filterRelease, undefined, true)
        .then(async function () {
            await extractPackage(archivedPackage, destination);
            vscode.window.showInformationMessage(`NukeTools: Package updated: ${pkg.name}`);
            return pkg;
        })
        .catch(function (err: { message: unknown }) {
            vscode.window.showWarningMessage(
                "NukeTools: Failed to download package from GitHub: " + err.message
            );
            return null;
        });
}
