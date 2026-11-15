import * as fs from "fs";
import * as path from "path";

import * as vscode from "vscode";

import * as packages from "./packages";
import { getConfig } from "./config";
import { NUKE_DIR } from "./constants";

const MENU_PY = path.join(NUKE_DIR, "menu.py");

/**
 * Add a menu import to the menu.py file in the .nuke folder.
 *
 * Only adds the import if it doesn't already exist.
 *
 * @param importText The import statement to add to the menu.py file.
 */
export function addMenuImport(importText: string): void {
    if (fs.existsSync(MENU_PY)) {
        const fileContent = fs.readFileSync(MENU_PY, "utf-8");
        if (!fileContent.includes(importText)) {
            fs.appendFileSync(MENU_PY, `\n${importText}\n`);
        }
    } else {
        fs.writeFileSync(MENU_PY, importText);
    }
}

/**
 * Cleanup the legacy NukeServerSocket import from the menu.py file.
 *
 * NukeServerSocket < 1.0.0 used to have a different import statement which is now deprecated
 * and should be removed from the menu.py file if it exists.
 */
function cleanupLegacyNukeServerSocket(): void {
    if (!fs.existsSync(MENU_PY)) {
        return;
    }

    const fileContent = fs.readFileSync(MENU_PY, "utf-8");

    const legacyImport = "from NukeTools import NukeServerSocket";

    if (!fileContent.includes(legacyImport)) {
        return;
    }

    fs.writeFileSync(MENU_PY, fileContent.replace(legacyImport, ""));
}

/**
 * Add nukeserversocket to the .nuke folder and import it inside the menu.py
 */
export async function addNukeServerSocket(): Promise<boolean> {
    if (!(await packages.addPackage(packages.PackageIds.nukeServerSocket))) {
        return false;
    }
    cleanupLegacyNukeServerSocket();
    addMenuImport(
        "from NukeTools.nukeserversocket import nukeserversocket\nnukeserversocket.install_nuke()"
    );
    return true;
}

const NSS_LAST_CHECK = "nss.lastUpdateCheck";
const NSS_SKIPPED_VERSION = "nss.skippedVersion";
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

/**
 * Read the version of the nukeserversocket installed by NukeTools.
 *
 * @returns the version, or undefined if nukeserversocket was not installed by NukeTools.
 */
function installedNukeServerSocketVersion(): string | undefined {
    const pkg = packages.packageMap.get(packages.PackageIds.nukeServerSocket)!;
    try {
        const pyproject = fs.readFileSync(path.join(pkg.destination, "pyproject.toml"), "utf-8");
        return pyproject.match(/^version\s*=\s*"([^"]+)"/m)?.[1];
    } catch {
        return undefined;
    }
}

/**
 * Notify the user when a newer nukeserversocket release is available.
 *
 * Checks at most once a day. Network errors are silent so offline machines never see a popup.
 */
export async function checkNukeServerSocketUpdate(context: vscode.ExtensionContext): Promise<void> {
    if (!getConfig("packages.checkNukeServerSocketUpdates")) {
        return;
    }

    const now = Date.now();
    if (now - context.globalState.get(NSS_LAST_CHECK, 0) < ONE_DAY_MS) {
        return;
    }

    const installed = installedNukeServerSocketVersion();
    if (!installed) {
        return;
    }

    // Set before fetching so a failing network does not trigger a request on every activation.
    await context.globalState.update(NSS_LAST_CHECK, now);

    let release;
    try {
        release = await packages.fetchLatestRelease(packages.PackageIds.nukeServerSocket);
    } catch {
        return;
    }

    const latest = release.tag_name.replace(/^v/, "");
    if (!packages.isNewerVersion(latest, installed)) {
        return;
    }
    if (context.globalState.get(NSS_SKIPPED_VERSION) === latest) {
        return;
    }

    const choice = await vscode.window.showInformationMessage(
        `NukeTools: nukeserversocket ${latest} is available (installed: ${installed}).`,
        "Update",
        "Release Notes",
        "Skip This Version"
    );

    if (choice === "Update") {
        if (await addNukeServerSocket()) {
            vscode.window.showInformationMessage(
                `NukeTools: Restart Nuke to load nukeserversocket ${latest}.`
            );
        }
    } else if (choice === "Release Notes") {
        vscode.env.openExternal(vscode.Uri.parse(release.html_url));
    } else if (choice === "Skip This Version") {
        await context.globalState.update(NSS_SKIPPED_VERSION, latest);
    }
}
