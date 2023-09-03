import * as vscode from "vscode";

import { sendCommand } from "../socket";

async function askNuke(text: string) {
    return sendCommand(JSON.stringify({ text: text, file: "" }));
}

export class NukeCompletionProvider implements vscode.CompletionItemProvider {
    provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): vscode.ProviderResult<
        vscode.CompletionItem[] | vscode.CompletionList<vscode.CompletionItem>
    > {
        const linePrefix = document.lineAt(position).text.substring(0, position.character);
        if (linePrefix.endsWith("nuke.toNode(")) {
            return this.getAllNodes();
        }
        return [];
    }

    private async getAllNodes(): Promise<vscode.CompletionItem[]> {
        return askNuke("[n.name() for n in nuke.allNodes()]").then((data) => {
            const nodes = JSON.parse(data.message.replace(/'/g, '"'));

            const items: vscode.CompletionItem[] = [];
            for (const node of nodes) {
                items.push(new vscode.CompletionItem(`"${node}"`, vscode.CompletionItemKind.Class));
            }
            return items;
        });
    }
}
