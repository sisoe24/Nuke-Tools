import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { sendCommand } from "./socket";

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

export class NukeNodesInspectorProvider implements vscode.TreeDataProvider<Dependency> {
    private _onDidChangeTreeData: vscode.EventEmitter<Dependency | undefined | null | void> =
        new vscode.EventEmitter<Dependency | undefined | null | void>();

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element: Dependency): vscode.TreeItem | Thenable<vscode.TreeItem> {
        return element;
    }

    private async sendMessage() {
        return await sendCommand(
            JSON.stringify({ text: "import json;json.dumps({n.name():n.Class() for n in nuke.allNodes()})", file: "file.node_inspector" })
        );
    }
    async getChildren(element?: Dependency | undefined): Promise<vscode.ProviderResult<Dependency[]>> {
        const items = [];
        const msg = await this.sendMessage();
        console.log("🚀 ~ file: ~ msg:", msg);
        // send an tcp message to nukeserversocket
        for (let i = 0; i <= 10; i++) {
            items.push(new Dependency(`${i}yolo`, "sbolo", vscode.TreeItemCollapsibleState.None));
        }
        return items;
    }
}

export class NodeDependenciesProvider implements vscode.TreeDataProvider<Dependency> {
    private _onDidChangeTreeData: vscode.EventEmitter<Dependency | undefined | null | void> =
        new vscode.EventEmitter<Dependency | undefined | null | void>();

    readonly onDidChangeTreeData: vscode.Event<Dependency | undefined | null | void> =
        this._onDidChangeTreeData.event;

    constructor(private workspaceRoot: string) {}

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
            if (this.pathExists(packageJsonPath)) {
                return Promise.resolve(this.getDepsInPackageJson(packageJsonPath));
            } else {
                vscode.window.showInformationMessage("Workspace has no package.json");
                return Promise.resolve([]);
            }
        }
    }

    private getStuff(): Dependency[] {
        return [new Dependency("yolo", "sbolo", vscode.TreeItemCollapsibleState.None)];
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
