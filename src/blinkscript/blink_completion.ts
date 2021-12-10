import * as path from "path";
import { readFileSync } from "fs";

import * as vscode from "vscode";

/**
 * Create the array for the completion item provider.
 *
 * Each item would have a label and an optional documentation that could be an
 * empty string. All of items will be of kind `Property`.
 *
 * @param object object of key value pair with the label and description for the
 * item completion. eg `{ePixelWise: "This method.."}`
 *
 * @returns a `CompletionItem` array.
 */
export function createCompletions(object: { [s: string]: string }): vscode.CompletionItem[] {
    const completionArray: vscode.CompletionItem[] = [];
    for (const [key, description] of Object.entries(object)) {
        const item = new vscode.CompletionItem(key, vscode.CompletionItemKind.Property);
        item.documentation = description;
        completionArray.push(item);
    }
    return completionArray;
}

const completionFile = JSON.parse(
    readFileSync(
        path.join(path.resolve(__dirname, "../.."), "language", "blink_completion.json"),
        "utf-8"
    )
);

export class BlinkScriptCompletionProvider implements vscode.CompletionItemProvider {
    provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): vscode.ProviderResult<
        vscode.CompletionItem[] | vscode.CompletionList<vscode.CompletionItem>
    > {
        const linePrefix = document.lineAt(position).text.substr(0, position.character);

        if (linePrefix.match(/kernel\s\w+\s*:\s*\w+(?!<)$/)) {
            return createCompletions(completionFile.kernelsType);
        } else if (linePrefix.match(/kernel\s\w+\s*:\s*\w+\s*</)) {
            return createCompletions(completionFile.kernelGranularity);
        } else if (linePrefix.match(/Image</)) {
            return createCompletions(completionFile.imageAccess);
        }

        return null;
    }
}
