import * as vscode from "vscode";

import * as fs from "fs";
import * as path from "path";

import { isConnected, sendCommand } from "../socket";

const setupCodeSnippet = (knobFile: KnobFile) => `
nuketools_tab = nuke.Tab_Knob('nuketools', 'NukeTools')

node = nuke.toNode('${knobFile.node}')

if not node.knob('nuketools'):
    node.addKnob(nuketools_tab)

script_knob = nuke.PyScript_Knob('${knobFile.knob}_${knobFile.id}', '${knobFile.knob}')

if not node.knob('${knobFile.knob}'):
    node.addKnob(script_knob)
`;

const syncKnobChangedSnippet = (knobFile: KnobFile) => `
node = nuke.toNode('${knobFile.node}')
node.knob('knobChanged').setValue('''${knobFile.content()}''')
`;

const syncKnobCodeSnippet = (knobFile: KnobFile) => `
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

// get vscode workspace path
function getWorkspacePath() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders) {
        return workspaceFolders[0].uri.fsPath;
    }
    return "";
}

// create .nuketools directory in the workspace
const KNOBS_DIR = path.join(getWorkspacePath(), ".nuketools");

async function sendToNuke(text: string) {
    return await sendCommand(
        JSON.stringify({
            text: text,
            file: "",
            formatText: "0",
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

    /**
     * Constructor for the KnobFile class.
     *
     * @param knobFile name to the knob file
     */
    constructor(knobFile: string) {
        this.filename = path.basename(knobFile);
        this.path = knobFile;

        const split = this.filename.split("_");
        this.node = split[0];
        this.nodeClass = split[1];
        this.knob = split[2];
        this.id = split[3].replace(".py", "");
    }

    /**
     * The signature of the knob file.
     *
     * @param node node name
     * @param nodeClass node class
     * @param knob knob name
     * @param id uuid of the knob
     * @returns the signature of the knob file
     */
    private static fileSignature(node: string, nodeClass: string, knob: string, id: string) {
        return `${node}_${nodeClass}_${knob.replace(" ", "_")}_${id}`;
    }

    /**
     * Create a new knob file.
     *
     * @param item A dictionary with the node name and class.
     * @param knobName The name of the knob.
     * @returns A new knob file.
     */
    static create(item: { node: string; class: string }, knobName: string) {
        const fileSignature = KnobFile.fileSignature(
            item.node,
            item.class,
            knobName,
            Date.now().toString()
        );

        const filePath = path.join(KNOBS_DIR, `${fileSignature}.py`);
        return new KnobFile(filePath);
    }

    /**
     * Set the new name of the node in the knob file.
     *
     * @param name New node name
     * @returns New file name
     */
    newName(name: string) {
        return `${KnobFile.fileSignature(name, this.nodeClass, this.knob, this.id)}.py`;
    }

    /**
     * Get the content of the knob file.
     *
     * @returns The content of the knob file.
     */
    content() {
        return fs.readFileSync(path.join(KNOBS_DIR, this.path), { encoding: "utf-8" });
    }
}

/**
 * An object containing the context value and the icon of the tree item.
 */
const itemContext = {
    node: { context: "node", icon: "symbol-misc" },
    knob: { context: "knob", icon: "symbol-file" },
};

/**
 * A tree node item representing a dependency. The dependency can be a Node or a Knob.
 */
class Dependency extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        private version: string,
        context: { context: string; icon: string },
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = `${this.label}-${this.version}`;
        this.description = this.version;
        this.contextValue = context.context;

        // TODO: add command only to knobs
        this.command = {
            command: "nuke-tools.on_itemClicked",
            title: label,
            arguments: [this],
        };
        this.iconPath = new vscode.ThemeIcon(context.icon);
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
     * Sync the files in the .nuketools directory with the nodes in Nuke. Because the user can rename
     * a node in Nuke, when syncing, the file will be renamed in the .nuketools directory.
     *
     * The new name is obtained from the return of the socket command. The socket command returns the
     * name of the node or 'False' as a string if the node doesn't exist.
     */
    async syncNodes(): Promise<void> {
        const files = osWalk(KNOBS_DIR);
        const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

        // TODO: send all the code at once and then rename the files.

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (!file.endsWith(".py")) {
                continue;
            }

            const knobFile = new KnobFile(file);
            const result = await sendToNuke(syncNodeSnippet(knobFile));
            if (result.error) {
                vscode.window.showErrorMessage(`Failed to sync ${file}: ${result.errorMessage}`);
                continue;
            }
            const newName = knobFile.newName(result.message);

            try {
                fs.renameSync(file, path.join(KNOBS_DIR, newName));
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to rename ${file} to ${newName}: ${error}`);
            }

            sleep(1000);
        }

        this.refresh();
    }

    /**
     * Sync the knob code content inside Nuke. When the knob is 'knobChanged', the code will be
     * act differently since it does not need to be setup as a knob.
     *
     * @param item A Node dependency item.
     */
    syncKnob(item: Dependency): void {
        const knobFile = new KnobFile(item.label);

        const codeSnippet =
            knobFile.knob === "knobChanged"
                ? syncKnobChangedSnippet(knobFile)
                : syncKnobCodeSnippet(knobFile);

        sendToNuke(codeSnippet);
    }

    /**
     * Add a new knob to a node.
     *
     * The knob is created as a new file in the .nuketools directory and it will follow the signature of
     * KnobFile.fileSignature. If the knob already exists, it will not be created.
     *
     * To create a new knob, the user will be prompted to enter the name of the knob. The name will be used
     * to create the file and the knob in Nuke.
     *
     * @param item A Node dependency item.
     */
    async addKnob(item: Dependency): Promise<void> {
        const knobName = await vscode.window.showInputBox({
            title: "Add knob",
            placeHolder: "Enter the name of the knob",
            prompt: "Use only alphanumeric characters and underscores.",
        });
        if (!knobName) {
            return;
        }

        const knobFile = KnobFile.create(
            { node: item.label, class: item.description as string },
            knobName
        );

        const files = osWalk(KNOBS_DIR);
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

        this.refresh();

        // If the knob is knobChanged, we don't need to send the code to Nuke.
        // because the knob already exists.
        if (knobName === "knobChanged") {
            return;
        }

        sendToNuke(setupCodeSnippet(knobFile));
    }

    /**
     * Open the file in the editor when the user clicks on it only if it's a python file.
     *
     * @param item The item that was clicked
     */
    itemClicked(item: Dependency): void {
        if (item.label.endsWith(".py")) {
            vscode.window.showTextDocument(vscode.Uri.file(path.join(KNOBS_DIR, item.label)), {
                preview: false,
            });
        }
    }

    getTreeItem(element: Dependency): vscode.TreeItem | Thenable<vscode.TreeItem> {
        return element;
    }

    /**
     * Get the knobs files for the node in the tree view.
     *
     * The function will iterate over all the files in the .nuketools folder and check if
     * the file name starts with the node name and class. If it does, will add it to the list.
     *
     * @param element The node that was clicked
     * @returns A list of Dependency objects that represent the knobs files.
     */
    private getKnobs(element: Dependency) {
        const items: vscode.ProviderResult<Dependency[]> = [];
        osWalk(KNOBS_DIR).forEach((file) => {
            const filename = path.basename(file);
            // label is the node name and description is the node class
            if (filename.startsWith(`${element.label}_${element.description}`)) {
                items.push(
                    new Dependency(
                        filename,
                        "",
                        itemContext.knob,
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
     * The nodes are retrieved by sending python code to the Nuke server socket.
     *
     * @returns A list of Dependency objects that represent the nodes in the current Nuke script.
     */
    private async getNodes(): Promise<Dependency[]> {
        const data = await sendToNuke(
            "import nuke;import json;json.dumps({n.name():n.Class() for n in nuke.allNodes()})"
        );

        // If the connection was refused, it means that Nuke server socket is not running.
        if (data.error) {
            vscode.window.showErrorMessage(`Failed to get nodes: ${data.errorMessage}`);
            return [];
        }

        if (!data.message) {
            vscode.window.showErrorMessage(`Failed to get nodes: no message received from Nuke`);
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
                    itemContext.node,
                    vscode.TreeItemCollapsibleState.Collapsed
                )
            );
        }
        return items;
    }

    getChildren(element?: Dependency): Thenable<Dependency[]> {
        if (!fs.existsSync(KNOBS_DIR)) {
            fs.mkdirSync(KNOBS_DIR);
        }
        if (element) {
            return Promise.resolve(this.getKnobs(element));
        }
        return Promise.resolve(this.getNodes());
    }
}
