import { readFileSync } from "fs";
import * as path from "path";
import * as vscode from "vscode";

const fileSnippet = readFileSync(
    path.join(path.resolve(__dirname, "../.."), "demo/blink_sample.blink"),
    "utf-8"
);

export class BlinkSnippets implements vscode.CompletionItemProvider {
    provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): vscode.ProviderResult<
        vscode.CompletionItem[] | vscode.CompletionList<vscode.CompletionItem>
    > {
        const kernelCompletion = new vscode.CompletionItem("kernel");
        kernelCompletion.documentation = new vscode.MarkdownString("Start up kernel template");
        kernelCompletion.insertText = new vscode.SnippetString(fileSnippet);

        return [kernelCompletion];
    }
}
