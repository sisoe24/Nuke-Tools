import * as fs from "fs";
import * as https from "https";
import path = require("path");
import * as vscode from "vscode";

interface GithubRelease {
    zipball_url?: string;
    tag_name: string;
    name: string;
}

const PackagesLog = path.join(path.resolve(__dirname, ".."), "github_packages.json");

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
        fs.writeFileSync(PackagesLog, JSON.stringify(versions, null, 4));
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

    if (!fs.existsSync(PackagesLog)) {
        console.log("no log file");
        fetchLatestRelease(packages);
        return;
    }

    const timestamp = JSON.parse(fs.readFileSync(PackagesLog, "utf8"))["lastCheck"];

    const lastUpdated = new Date(timestamp).getTime();

    const now = new Date().getTime();

    if (now - lastUpdated > frequency) {
        fetchLatestRelease(packages);
        return;
    }

    console.log("no need to fetch");
}
