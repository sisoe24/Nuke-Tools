import * as path from "path";
import * as vscode from "vscode";

import { readFileSync } from "fs";
import { PACKAGE_RESOURCES_PATH } from "../constants";


/**
 * Sample blinkscript file. same as Nuke default blinkscript node.
 */
export const saturationTemplate = readFileSync(
    path.join(PACKAGE_RESOURCES_PATH, "language", "saturation_sample.blink"),
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
