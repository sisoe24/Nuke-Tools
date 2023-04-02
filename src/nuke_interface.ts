import * as vscode from "vscode";

import * as fs from "fs";
import * as path from "path";
import * as uuid from "uuid";

import * as util from "./utils";
import { sendCommand } from "./socket";

// TODO: icons: add, sync, delete, save, refresh, file-code, node

const setupCodeSnippet = (knobFile: KnobFile) => `
nuketools_tab = nuke.Tab_Knob('nuketools', 'NukeTools')

node = nuke.toNode('${knobFile.node}')

if not node.knob('nuketools'):
    node.addKnob(nuketools_tab)

script_knob = nuke.PyScript_Knob('${knobFile.knob}_${knobFile.id}', '${knobFile.knob}')

if not node.knob('${knobFile.knob}'):
    node.addKnob(script_knob)
`;

const saveCodeSnippet = (knobFile: KnobFile) => `
node = nuke.toNode('${knobFile.node}')
node.knob('${knobFile.knob}_${knobFile.id}').setValue('''${knobFile.content()}''')
`;

const syncNodeSnippet = (knobFile: KnobFile) => `
def getnodes():
    for node in nuke.allNodes('${knobFile.nodeClass}'):
        for knob in node.allKnobs():
            if knob.name() == '${knobFile.knob}_${knobFile.id}':
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
        results.push(path.join(dir, file));
    });
    return results;
};

// TODO: path should be inside the workspace
const NUKETOOLS = path.join(util.extensionPath(), ".nuketools");

// TODO: refactor this
function sendToNuke(text: string) {
    return sendCommand(
        JSON.stringify({
            text: text,
            file: "",
        })
    );
}

class KnobFile {
    knob: string;
    node: string;
    nodeClass: string;
    id: string;
    path: string;
    filename: string;

    constructor(knobFile: string) {
        console.log("🚀 :", knobFile);
        this.filename = path.basename(knobFile);
        this.path = knobFile;

        const split = this.filename.split("_");
        this.node = split[0];
        this.nodeClass = split[1];
        this.knob = split[2];
        this.id = split[3].replace(".py", "");
    }

    private static fileSignature(node: string, nodeClass: string, knob: string, id: string) {
        return `${node}_${nodeClass}_${knob.replace(" ", "_")}_${id}`;
    }

    static create(item: { node: string; class: string }, knobName: string) {
        const fileSignature = KnobFile.fileSignature(item.node, item.class, knobName, uuid.v4());

        const filePath = path.join(NUKETOOLS, `${fileSignature}.py`);
        return new KnobFile(filePath);
    }

    newName(name: string) {
        return KnobFile.fileSignature(name, this.nodeClass, this.knob, this.id);
    }

    content() {
        return fs.readFileSync(path.join(NUKETOOLS, this.path), { encoding: "utf-8" });
    }
}

class Dependency extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        private version: string,
        contextValue: string,
        icon: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = `${this.label}-${this.version}`;
        this.description = this.version;
        this.contextValue = contextValue;
        this.command = {
            command: "nuke-tools.on_itemClicked",
            title: label,
            arguments: [this],
        };
        this.iconPath = {
            light: path.join(util.getResourcesPath("icons"), "light", `${icon}.svg`),
            dark: path.join(util.getResourcesPath("icons"), "dark", `${icon}.svg`),
        };
    }
}

export class NukeNodesInspectorProvider implements vscode.TreeDataProvider<Dependency> {
    private _onDidChangeTreeData: vscode.EventEmitter<Dependency | undefined | null | void> =
        new vscode.EventEmitter<Dependency | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<Dependency | undefined | null | void> =
        this._onDidChangeTreeData.event;

    /**
     * Refresh the tree view.
     */
    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    /**
     * Sync the nodes in Nuke with the ones in the .nuketools directory.
     *
     * If user renamed a node in Nuke, the node will be renamed in the .nuketools directory.
     */
    async syncNodes(): Promise<void> {
        const files = osWalk(NUKETOOLS);
        const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

        for (let i = 0; i < files.length; i++) {
            const file = files[i];

            const knobFile = new KnobFile(file);
            const result = await sendToNuke(syncNodeSnippet(knobFile));
            if (result.message === "False") {
                continue;
            }
            const newName = knobFile.newName(result.message);

            try {
                fs.renameSync(file, path.join(NUKETOOLS, newName));
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to rename ${file} to ${newName}: ${error}`);
            }

            sleep(1000);
        }

        this.refresh();
    }

    /**
     * Save the knob code content inside Nuke.
     *
     * @param item A Node dependency item.
     * @returns
     */
    saveKnob(item: Dependency): void {
        sendToNuke(saveCodeSnippet(new KnobFile(item.label)));
    }

    /**
     * Add a new knob to a node.
     *
     * The knob is created as a new file in the .nuketools directory and it will have the following format:
     * nodename_nodeclass_knobname_uuid.py. If the knob already exists, it will not be created.
     *
     * To create a new knob, the user will be prompted to enter the name of the knob. The name will be used
     * to create the file and the knob in Nuke.
     *
     * @param item A Node dependency item.
     */
    async addKnob(item: Dependency): Promise<void> {
        const knobName = await vscode.window.showInputBox();
        if (!knobName) {
            return;
        }

        const knobFile = KnobFile.create(
            { node: item.label, class: item.description as string },
            knobName
        );

        const files = osWalk(NUKETOOLS);
        for (let i = 0; i < files.length; i++) {
            const file = files[i];

            // Get the knob name file parts without the id to check if the knob already exists.
            const knobFileName = knobFile.filename.split("_").slice(0, 3).join("_");

            if (path.basename(file).startsWith(knobFileName)) {
                vscode.window.showErrorMessage("Knob already exists");
                return;
            }
        }

        fs.writeFileSync(knobFile.path, "");
        vscode.window.showTextDocument(vscode.Uri.file(knobFile.path), { preview: false });

        sendToNuke(setupCodeSnippet(knobFile));

        this.refresh();
    }

    /**
     * Open the file in the editor when the user clicks on it only if it's a python file.
     *
     * @param item The item that was clicked
     */
    itemClicked(item: Dependency): void {
        if (item.label.endsWith(".py")) {
            vscode.window.showTextDocument(vscode.Uri.file(path.join(NUKETOOLS, item.label)), {
                preview: false,
            });
        }
    }

    getTreeItem(element: Dependency): vscode.TreeItem | Thenable<vscode.TreeItem> {
        return element;
    }

    /**
     * Get the knobs files for the node that was clicked.
     *
     * The function will iterate over all the files in the .nuketools folder and check if
     * the file name starts with the node name and class. If it does, will add it to the list.
     *
     * @param element The node that was clicked
     * @returns A list of Dependency objects that represent the knobs files.
     */
    private getKnobs(element: Dependency) {
        const items: vscode.ProviderResult<Dependency[]> = [];
        osWalk(NUKETOOLS).forEach((file) => {
            const filename = path.basename(file);
            // label is the node name and description is the node class
            if (filename.startsWith(`${element.label}_${element.description}`)) {
                items.push(
                    new Dependency(
                        filename,
                        "",
                        "knob",
                        "file-code",
                        vscode.TreeItemCollapsibleState.None
                    )
                );
            }
        });
        return items;
    }

    /**
     * Get the nodes in the current Nuke script.
     *
     * The nodes are retrieved by sending a python script to the Nuke server socket.
     *
     * @returns A list of Dependency objects that represent the nodes in the current Nuke script.
     */
    private async getNodes(): Promise<Dependency[]> {
        const data = await sendToNuke(
            "import nuke;import json;json.dumps({n.name():n.Class() for n in nuke.allNodes()})"
        );

        // If the connection was refused, it means that Nuke server socket is not running.
        if (data.message === "Connection refused") {
            return [];
        }

        // For some reason, the JSON is wrapped in single quotes, so we need to remove them
        const nodes: { string: string } = JSON.parse(data.message.replace(/'/g, ""));

        const items: vscode.ProviderResult<Dependency[]> = [];
        for (const [key, value] of Object.entries(nodes)) {
            items.push(
                new Dependency(
                    key,
                    value,
                    "node",
                    "dependency",
                    vscode.TreeItemCollapsibleState.Collapsed
                )
            );
        }
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
