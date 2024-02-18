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

type GithubPackages = {
    lastCheck: string;
    packages: { [key: string]: string };
};

/**
 * Fetch the latest release of a package from github api and save it to the log file.
 * 
 * @see GithubPackages
 * @param packages a list of packages to fetch the latest release
 */
async function fetchLatestRelease(packages: string[]): Promise<void> {
    console.log("fetching latest release");

    const fetch = async () => {
        const versions: GithubPackages = {
            lastCheck: new Date().toISOString(),
            packages: {},
        };

        for (const key of packages) {
            try {
                const releaseData = await getLatestRelease(key);
                versions["packages"][key] = releaseData["tag_name"];
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

export function fetchPackagesLatestVersion(packages: string[], frequency: number = T.week): void {
    console.log("try fetching packages");

    if (!fs.existsSync(ASSETS_LOG_PATH)) {
        console.log("no log file");
        fetchLatestRelease(packages);
        return;
    }

    const timestamp = JSON.parse(fs.readFileSync(ASSETS_LOG_PATH, "utf8"))["lastCheck"];

    const lastUpdated = new Date(timestamp).getTime();

    const now = new Date().getTime();

    if (now - lastUpdated > frequency) {
        fetchLatestRelease(packages);
        return;
    }

    console.log("no need to fetch");
}
