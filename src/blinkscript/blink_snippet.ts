import { readFileSync } from "fs";
import * as path from "path";
import * as vscode from "vscode";

/**
 * Sample blinkscript file. same as Nuke default blinkscript node.
 */
const saturationTemplate = readFileSync(
    path.join(path.resolve(__dirname, "../.."), "demo/saturation_sample.blink"),
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
        kernelCompletion.documentation = new vscode.MarkdownString("Saturation sample script.");
        kernelCompletion.insertText = new vscode.SnippetString(saturationTemplate);

        return [kernelCompletion];
    }
}
