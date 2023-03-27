import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { sendCommand } from "./socket";
import crypto = require("crypto");

class Dependency extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        private version: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = `${this.label}-${this.version}`;
        this.description = this.version;
    }

    iconPath = {
        light: path.join(__filename, "..", "..", "resources", "light", "dependency.svg"),
        dark: path.join(__filename, "..", "..", "resources", "dark", "dependency.svg"),
    };
}

const setupCode = (knob: string, id: string, node: string) => `
import nuke
import random

script_knob = nuke.PyScript_Knob('nuketools_${node}_${knob}_${id}.py')
script_knob.setLabel('${knob}')

node = nuke.toNode('${node}')
knob = node.knob('${knob}')
if not knob:
    node.addKnob(script_knob)
    knob = node.knob('test')
`;

const syncCode = (node: string, knob: string, content: string) => `
nuke.toNode('${node}').knob('${knob}').setValue('''${content}''')
`;

/**
 * Walk recursively a directory to get all of its files.
 *
 * @param dir Path for the directory to parse.
 * @returns A list of files
 */
const osWalk = function (dir: string): string[] {
    let results: string[] = [];

    fs.readdirSync(dir).forEach(function (file) {
        file = dir + path.sep + file;
        results.push(file);
    });
    return results;
};

const PATH = "/Users/virgilsisoe/Developer/vscode/work/Nuke-Tools/.nuketools";

export class NukeNodesInspectorProvider implements vscode.TreeDataProvider<Dependency> {
    private _onDidChangeTreeData: vscode.EventEmitter<Dependency | undefined | null | void> =
        new vscode.EventEmitter<Dependency | undefined | null | void>();

    constructor() {
        vscode.commands.registerCommand("nuke-tools.on_item_clicked", (r) => this.item_clicked(r));
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    async syncKnob(item: Dependency) {
        if (item.label.endsWith(".py")) {
            const filePath = path.join(PATH, item.label);
            const file = fs.readFileSync(filePath, { encoding: "utf-8" });
            const fileName = item.label.split("_");
            console.log("🚀 ~ :", fileName)
            const data = {
                text: syncCode(fileName[0], `nuketools_${item.label}`, file),
                file: "",
            };
            sendCommand(JSON.stringify(data));
        }
    }

    async addKnob(item: Dependency): Promise<void> {
        let hash = crypto.createHash("md5").update(item.label).digest("hex");

        const knobName = await vscode.window.showInputBox();
        const path = `${PATH}/${item.label}_${knobName}_${hash}.py`;

        fs.writeFileSync(path, "");
        vscode.window.showTextDocument(vscode.Uri.file(path), { preview: false });
        const data = {
            text: setupCode(knobName as string, hash, item.label),
            file: "",
        };
        sendCommand(JSON.stringify(data));
    }

    getTreeItem(element: Dependency): vscode.TreeItem | Thenable<vscode.TreeItem> {
        // return element;
        let title = element.label ? element.label.toString() : "";
        let result = new vscode.TreeItem(title, element.collapsibleState);
        // here we add our command which executes our memberfunction
        result.command = {
            command: "nuke-tools.on_item_clicked",
            title: title,
            arguments: [element],
        };
        return result;
    }

    item_clicked(item: Dependency) {
        // this will be executed when we click an item
        console.log("🚀 item clicked:", item);
        if (item.label.endsWith(".py")) {
            vscode.window.showTextDocument(vscode.Uri.file(path.join(PATH, item.label)), {
                preview: false,
            });
        }
    }

    private async sendMessage() {
        const results = sendCommand(
            JSON.stringify({
                text: "import nuke;import json;json.dumps({n.name():n.Class() for n in nuke.allNodes()})",
                file: "",
            })
        );
        return (await results).message.replace(/'/g, "");
    }

    async getChildren(
        element?: Dependency | undefined
    ): Promise<vscode.ProviderResult<Dependency[]>> {
        if (element) {
            const items: vscode.ProviderResult<Dependency[]> = [];
            osWalk(PATH).forEach((file) => {
                const filename = path.basename(file);
                if (filename.startsWith(element.label)) {
                    items.push(new Dependency(filename, "", vscode.TreeItemCollapsibleState.None));
                }
            });
            return items;
        } else {
            const items: vscode.ProviderResult<Dependency[]> = [];
            const data = JSON.stringify({
                text: "import nuke;import json;json.dumps({n.name():n.Class() for n in nuke.allNodes()})",
                file: "",
            });

            let result: { string: string };

            const msg = await sendCommand(data).then((value) => {
                result = JSON.parse(value.message.replace(/'/g, ""));
            });

            for (const [key, value] of Object.entries(result)) {
                items.push(new Dependency(key, value, vscode.TreeItemCollapsibleState.Collapsed));
            }

            console.log("🚀 items:", items);
            return items;
        }
        return [];
    }
}

export class NodeDependenciesProvider implements vscode.TreeDataProvider<Dependency> {
    private _onDidChangeTreeData: vscode.EventEmitter<Dependency | undefined | null | void> =
        new vscode.EventEmitter<Dependency | undefined | null | void>();

    readonly onDidChangeTreeData: vscode.Event<Dependency | undefined | null | void> =
        this._onDidChangeTreeData.event;

    workspaceRoot: string;

    constructor() {
        this.workspaceRoot = "/Users/virgilsisoe/Developer/vscode/work/Nuke-Tools";
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: Dependency): vscode.TreeItem {
        return element;
    }

    getChildren(element?: Dependency): Thenable<Dependency[]> {
        if (!this.workspaceRoot) {
            vscode.window.showInformationMessage("No dependency in empty workspace");
            return Promise.resolve([]);
        }

        if (element) {
            return Promise.resolve(
                this.getDepsInPackageJson(
                    path.join(this.workspaceRoot, "node_modules", element.label, "package.json")
                )
            );
        } else {
            const packageJsonPath = path.join(this.workspaceRoot, "package.json");
            console.log("🚀 ~ packageJsonPath:", packageJsonPath);

            if (this.pathExists(packageJsonPath)) {
                return Promise.resolve(this.getDepsInPackageJson(packageJsonPath));
            } else {
                vscode.window.showInformationMessage("Workspace has no package.json");
                return Promise.resolve([]);
            }
        }
    }

    /**
     * Given the path to package.json, read all its dependencies and devDependencies.
     */
    private getDepsInPackageJson(packageJsonPath: string): Dependency[] {
        if (this.pathExists(packageJsonPath)) {
            const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf-8"));

            const toDep = (moduleName: string, version: string): Dependency => {
                if (this.pathExists(path.join(this.workspaceRoot, "node_modules", moduleName))) {
                    return new Dependency(
                        moduleName,
                        version,
                        vscode.TreeItemCollapsibleState.Collapsed
                    );
                } else {
                    return new Dependency(
                        moduleName,
                        version,
                        vscode.TreeItemCollapsibleState.None
                    );
                }
            };

            const deps = packageJson.dependencies
                ? Object.keys(packageJson.dependencies).map((dep) =>
                      toDep(dep, packageJson.dependencies[dep])
                  )
                : [];
            const devDeps = packageJson.devDependencies
                ? Object.keys(packageJson.devDependencies).map((dep) =>
                      toDep(dep, packageJson.devDependencies[dep])
                  )
                : [];
            return deps.concat(devDeps);
        } else {
            return [];
        }
    }

    private pathExists(p: string): boolean {
        try {
            fs.accessSync(p);
        } catch (err) {
            return false;
        }
        return true;
    }
}
