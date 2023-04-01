import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { sendCommand } from "./socket";
import crypto = require("crypto");
import uuid = require("uuid");
import * as util from "./utils";

class Dependency extends vscode.TreeItem {
    iconPath = {
        light: path.join(__filename, "..", "..", "resources", "icons", "light", "dependency.svg"),
        dark: path.join(__filename, "..", "..", "resources", "icons", "dark", "dependency.svg"),
    };
    contextValue = "dependency";

    constructor(
        public readonly label: string,
        private version: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = `${this.label}-${this.version}`;
        this.description = this.version;
    }
}

const setupCodeSnippet = (node: string, nodeClass: string, knob: string, id: string) => `
nuketools_tab = nuke.Tab_Knob('nuketools', 'NukeTools')

node = nuke.toNode('${node}')

if not node.knob('nuketools'):
    node.addKnob(nuketools_tab)

script_knob = nuke.PyScript_Knob('${knob}_${id}', '${knob}')

if not node.knob('${knob}'):
    node.addKnob(script_knob)
`;

const saveCodeSnippet = (node: string, knob: string, content: string) => `
nuke.toNode('${node}').knob('${knob}').setValue('''${content}''')
`;

const syncNodeSnippet = (node: string, nodeClass: string, knob: string, id: string) => `
def getnodes():
    for node in nuke.allNodes('${nodeClass}'):
        for knob in node.allKnobs():
            if knob.name() == '${knob}_${id}':
                return node.name()
    return False
print(getnodes())
`;

/**
 * Walk recursively a directory to get all of its files.
 *
 * @param dir Path for the directory to parse.
 * @returns A list of files
 */
const osWalk = function (dir: string): string[] {
    const results: string[] = [];

    fs.readdirSync(dir).forEach(function (file) {
        file = dir + path.sep + file;
        results.push(file);
    });
    return results;
};

const NUKETOOLS = path.join(util.extensionPath(), ".nuketools");

function sendData(text: string) {
    return sendCommand(
        JSON.stringify({
            text: text,
            file: "",
        })
    );
}

function renameFile(oldPath: string, newPath: string) {
    return new Promise<void>((resolve, reject) => {
        fs.rename(oldPath, newPath, (err) => {
            if (err) {
                reject(err);
            }
            resolve();
        });
    });
}

export class NukeNodesInspectorProvider implements vscode.TreeDataProvider<Dependency> {
    private _onDidChangeTreeData: vscode.EventEmitter<Dependency | undefined | null | void> =
        new vscode.EventEmitter<Dependency | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<Dependency | undefined | null | void> =
        this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    async syncNodes(): Promise<void> {
        const files = osWalk(NUKETOOLS);
        const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

        for (let i = 0; i < files.length; i++) {
            const file = files[i];

            const fileParts = path.basename(file).replace(".py", "").split("_");
            const result = await sendData(
                syncNodeSnippet(fileParts[0], fileParts[1], fileParts[2], fileParts[3])
            );
            if (result.message === "False") {
                continue;
            }
            const newName = `${result.message}_${fileParts[1]}_${fileParts[2]}_${fileParts[3]}.py`;
            renameFile(file, path.join(NUKETOOLS, newName));

            // Wait for a bit to make sure the sockets dont get flooded
            sleep(1000);
        }

        this.refresh();
    }

    async saveKnob(item: Dependency): Promise<void> {
        if (!item.label.endsWith(".py")) {
            return;
        }

        const fileParts = path.basename(item.label).split("_");
        sendData(
            saveCodeSnippet(
                fileParts[0],
                `${fileParts[2]}_${fileParts[3].replace(".py", "")}`,
                fs.readFileSync(path.join(NUKETOOLS, item.label), { encoding: "utf-8" })
            )
        );
    }

    async addKnob(item: Dependency): Promise<void> {
        const knobName = await vscode.window.showInputBox();
        if (!knobName) {
            return;
        }

        const fileHeader = `${item.label}_${item.description}_${knobName.replace(" ", "_")}`;
        const filePath = path.join(NUKETOOLS, `${fileHeader}_${uuid.v4()}.py`);

        const files = osWalk(NUKETOOLS);
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            // Check if the file already exists
            if (path.basename(file).startsWith(fileHeader)) {
                vscode.window.showErrorMessage("Knob already exists");
                return;
            }
        }

        fs.writeFileSync(filePath, "");
        vscode.window.showTextDocument(vscode.Uri.file(filePath), { preview: false });

        const fileParts = path.basename(filePath).split("_");
        sendData(
            setupCodeSnippet(
                item.label,
                fileParts[1],
                fileParts[2],
                fileParts[3].replace(".py", "")
            )
        );

        this.refresh();
    }

    getTreeItem(element: Dependency): vscode.TreeItem | Thenable<vscode.TreeItem> {
        const title = element.label ? element.label.toString() : "";
        const result = new vscode.TreeItem(title, element.collapsibleState);
        result.command = {
            command: "nuke-tools.on_item_clicked",
            title: title,
            arguments: [element],
        };
        return result;
    }

    itemClicked(item: Dependency) {
        if (item.label.endsWith(".py")) {
            vscode.window.showTextDocument(vscode.Uri.file(path.join(NUKETOOLS, item.label)), {
                preview: false,
            });
        }
    }

    private async getNodes(): Promise<Dependency[]> {
        const data = await sendData(
            "import nuke;import json;json.dumps({n.name():n.Class() for n in nuke.allNodes()})"
        );

        const nodes: { string: string } = JSON.parse(data.message.replace(/'/g, ""));

        const items: vscode.ProviderResult<Dependency[]> = [];
        for (const [key, value] of Object.entries(nodes)) {
            items.push(new Dependency(key, value, vscode.TreeItemCollapsibleState.Collapsed));
        }
        return items;
    }

    private getKnobs(element: Dependency) {
        const items: vscode.ProviderResult<Dependency[]> = [];
        osWalk(NUKETOOLS).forEach((file) => {
            const filename = path.basename(file);
            if (filename.startsWith(`${element.label}_${element.description}`)) {
                items.push(new Dependency(filename, "", vscode.TreeItemCollapsibleState.None));
            }
        });
        return items;
    }

    getChildren(element?: Dependency): Thenable<Dependency[]> {
        // TODO: check if nukeserversocket is running
        if (element) {
            return Promise.resolve(this.getKnobs(element));
        }
        return Promise.resolve(this.getNodes());
    }
}
