import { readFileSync } from "fs";
import * as path from "path";
import * as vscode from "vscode";

/**
 * Sample blinkscript file. same as Nuke default blinkscript node.
 */
export const saturationTemplate = readFileSync(
    path.join(path.resolve(__dirname, "../.."), "syntax/saturation_sample.blink"),
    "utf-8"
);

/**
 * BlinkScript snippet provider.
 */
export class BlinkSnippets implements vscode.CompletionItemProvider {
    /**
     * Initialize the snippet provider.
     * @returns an array of completion items.
     */
    provideCompletionItems(): vscode.CompletionItem[] {
        const kernelCompletion = new vscode.CompletionItem("kernel");
        kernelCompletion.documentation = "Saturation sample script.";
        kernelCompletion.insertText = new vscode.SnippetString(saturationTemplate);

        return [kernelCompletion];
    }
}
