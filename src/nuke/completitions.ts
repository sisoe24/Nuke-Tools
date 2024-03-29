import * as vscode from "vscode";

import { sendCommand } from "../socket";

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
        return sendCommand(
            JSON.stringify({ text: "[n.name() for n in nuke.allNodes()]", formatText: "0" })
        ).then((data) => {
            const nodes = JSON.parse(data.message.replace(/'/g, '"'));

            const items: vscode.CompletionItem[] = [];
            for (const node of nodes) {
                items.push(new vscode.CompletionItem(`"${node}"`, vscode.CompletionItemKind.Class));
            }
            return items;
        });
    }
}
