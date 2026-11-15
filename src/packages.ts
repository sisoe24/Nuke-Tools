import * as fs from "fs";
import * as os from "os";
import * as path from "path";

import * as vscode from "vscode";
import extract = require("extract-zip");

import { NUKE_TOOLS_DIR } from "./constants";

type PackageType = {
    name: string;
    destination: string;
};

export enum PackageIds {
    nukeServerSocket = "nukeserversocket",
    nukePythonStubs = "nuke-python-stubs",
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
async function extractPackage(source: string, destination: string): Promise<void> {
    await extract(source, { dir: destination + "-master" });

    if (fs.existsSync(destination)) {
        fs.rmSync(destination, { recursive: true });
    }
    fs.renameSync(destination + "-master", destination);
}

/**
 * Download the zip asset of the latest GitHub release of a package.
 *
 * @param name the package name. It is also the name of the repository and of the zip asset.
 * @param destination the path of the zip file to write.
 */
async function downloadLatestRelease(name: string, destination: string): Promise<void> {
    const response = await fetch(`https://api.github.com/repos/sisoe24/${name}/releases/latest`, {
        headers: { "User-Agent": "nuke-tools" },
    });
    if (!response.ok) {
        throw new Error(`GitHub API responded ${response.status}`);
    }

    const release = (await response.json()) as {
        assets: { name: string; browser_download_url: string }[];
    };
    const asset = release.assets.find((asset) => asset.name === `${name}.zip`);
    if (!asset) {
        throw new Error(`${name}.zip not found in the latest release`);
    }

    const download = await fetch(asset.browser_download_url);
    if (!download.ok) {
        throw new Error(`Download responded ${download.status}`);
    }
    fs.writeFileSync(destination, Buffer.from(await download.arrayBuffer()));
}

/**
 * Add a package to the .nuke/NukeTools folder.
 *
 * The latest release of the package is downloaded from GitHub and extracted
 * into the package destination, replacing any previous version.
 *
 * @param packageId the package to add
 * @returns the package, or null if it could not be added.
 */
export async function addPackage(packageId: PackageIds): Promise<PackageType | null> {
    const pkg = packageMap.get(packageId);

    if (!pkg) {
        throw new Error(`Package ${packageId} not found`);
    }

    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "nuke-tools-"));
    const archive = path.join(tmpDir, `${pkg.name}.zip`);

    try {
        await downloadLatestRelease(pkg.name, archive);
        await extractPackage(archive, pkg.destination);
    } catch (err) {
        vscode.window.showWarningMessage(
            `NukeTools: Failed to add package ${pkg.name}: ${(err as Error).message}`
        );
        return null;
    } finally {
        fs.rmSync(tmpDir, { recursive: true, force: true });
    }

    vscode.window.showInformationMessage(`NukeTools: Package added: ${pkg.name}`);
    return pkg;
}
