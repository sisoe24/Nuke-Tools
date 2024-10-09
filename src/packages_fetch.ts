import * as fs from "fs";
import * as https from "https";
import * as vscode from "vscode";

import { ASSETS_LOG_PATH } from "./constants";

interface GithubRelease {
    zipball_url?: string;
    tag_name: string;
    name: string;
}


function getLatestRelease(repo: string): Promise<GithubRelease> {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: "api.github.com",
            path: `/repos/sisoe24/${repo}/releases/latest`,
            method: "GET",
            headers: {
                "User-Agent": "Node.js https module",
            },
        };

        const req = https.request(options, (res) => {
            let data = "";

            res.on("data", (chunk) => {
                data += chunk;
            });

            res.on("end", () => {
                resolve(JSON.parse(data));
            });
        });

        req.on("error", (e) => {
            reject(e);
        });

        req.end();
    });
}

type IncludedPackages = {
    current: { [key: string]: string };
    lastest: { [key: string]: string };
};

type IncludedPackagesLog = {
    lastCheck: string;
    packages: IncludedPackages;
};

/**
 * Fetch the latest release of a package from github api and save it to the log file.
 * 
 * @see IncludedPackagesLog
 * @param packages a list of packages to fetch the latest release
 */
async function fetchLatestRelease(packages: IncludedPackages): Promise<void> {

    const fetch = async () => {
        const versions: IncludedPackagesLog = {
            lastCheck: new Date().toISOString(),
            packages: {
                current: packages.current,
                lastest: {},
            },
        };

        for (const key of Object.keys(packages.current)) {
            try {
                const releaseData = await getLatestRelease(key);
                versions["packages"]["lastest"][key] = releaseData["tag_name"];
            } catch (err) {
                vscode.window.showErrorMessage(err as string);
            }
        }

        return versions;
    };

    fetch().then((versions) => {
        fs.writeFileSync(ASSETS_LOG_PATH, JSON.stringify(versions, null, 4));
    });
}

const DAY = 24 * 60 * 60 * 1000;

const T = {
    day: DAY,
    week: 7 * DAY,
    month: 30 * DAY,
};

export function fetchPackagesLatestVersion(frequency: number = T.month): void {

    const logData = JSON.parse(fs.readFileSync(ASSETS_LOG_PATH, "utf8")) as IncludedPackagesLog;

    const lastUpdated = new Date(logData["lastCheck"]).getTime();
    const now = new Date().getTime();

    if (now - lastUpdated > frequency) {
        fetchLatestRelease(logData["packages"]);
        return;
    }

}
