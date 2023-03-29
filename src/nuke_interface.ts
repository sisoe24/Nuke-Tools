import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { sendCommand } from "./socket";
import crypto = require("crypto");
import uuid = require("uuid");
import * as util from "./utils";

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

const setupCodeSnippet = (knob: string, id: string, node: string) => `
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

const syncCodeSnippet = (node: string, knob: string, content: string) => `
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

const NUKETOOLS = path.join(util.extensionPath(), ".nuketools");

function sendData(text: string) {
    const data = {
        text: text,
        file: "",
    };
    return sendCommand(JSON.stringify(data));
}

export class NukeNodesInspectorProvider implements vscode.TreeDataProvider<Dependency> {
    private _onDidChangeTreeData: vscode.EventEmitter<Dependency | undefined | null | void> =
        new vscode.EventEmitter<Dependency | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<Dependency | undefined | null | void> =
        this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    async syncKnob(item: Dependency) {
        if (!item.label.endsWith(".py")) {
            return;
        }

        sendData(
            syncCodeSnippet(
                item.label.split("_")[0],
                `nuketools_${item.label}`,
                fs.readFileSync(path.join(NUKETOOLS, item.label), { encoding: "utf-8" })
            )
        );
    }

    async addKnob(item: Dependency): Promise<void> {
        const knobName = await vscode.window.showInputBox();
        const filePath = path.join(NUKETOOLS, `${item.label}_${knobName}_${uuid.v4()}.py`);

        fs.writeFileSync(filePath, "");
        vscode.window.showTextDocument(vscode.Uri.file(filePath), { preview: false });

        const fileParts = path.basename(filePath).split("/");
        sendData(setupCodeSnippet(fileParts[1], fileParts[2], item.label));
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

    itemClickde(item: Dependency) {
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
            if (filename.startsWith(element.label)) {
                items.push(new Dependency(filename, "", vscode.TreeItemCollapsibleState.None));
            }
        });
        return items;
    }

    getChildren(element?: Dependency): Thenable<Dependency[]> {
        if (element) {
            return Promise.resolve(this.getKnobs(element));
        }
        return Promise.resolve(this.getNodes());
    }
}
