import * as path from "path";
import { readFileSync } from "fs";

import * as vscode from "vscode";
import { PACKAGE_RESOURCES_PATH } from "../constants";

/**
 * The completion file for blinkscript.
 */
export const completionFile = JSON.parse(
    readFileSync(
        path.join(PACKAGE_RESOURCES_PATH, "language", "blinkscript_completion.json"),
        "utf-8"
    )
);

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

/**
 * Get completion items.
 *
 * This serves only for internal verification. Function will check if the key is
 * present and if yes will return the completion array. Otherwise will throw an error invalid key
 *
 * @param key key to check if present
 * @returns
 */
export function getCompletions(key: string): vscode.CompletionItem[] {
    if (!Object.prototype.hasOwnProperty.call(completionFile, key)) {
        throw new Error(`Invalid completion item: ${key}`);
    }
    return createCompletions(completionFile[key]);
}

const kernelType = {
    items: getCompletions("kernelTypes"),
    match: RegExp(/kernel\s\w+\s*:\s*\w+(?!<)$/),
};

const kernelGranularity = {
    items: getCompletions("kernelGranularity"),
    match: RegExp(/kernel\s\w+\s*:\s*\w+\s*</),
};

const imageAccess = {
    items: getCompletions("imageAccess"),
    match: RegExp(/Image\s*</),
};

/**
 * BlinkScript Completion Provider.
 *
 * The completion suggestion will be provided only when the cursor is in a specific
 * position.
 */
export class BlinkScriptCompletionProvider implements vscode.CompletionItemProvider {
    /**
     * Initialize the provider.
     *
     * @param document vscode document
     * @param position vscode cursor position
     * @returns an array with the completion items.
     */
    provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position
    ): vscode.CompletionItem[] | null {
        const linePrefix = document.lineAt(position).text.substring(0, position.character);

        /**
         * `kernel abc :` match
         */
        if (kernelType.match.test(linePrefix)) {
            return kernelType.items;
        }

        /**
         * `kernel abc : type <` match
         */
        if (kernelGranularity.match.test(linePrefix)) {
            return kernelGranularity.items;
        }

        /**
         * `Image <` match
         */
        if (imageAccess.match.test(linePrefix)) {
            return imageAccess.items;
        }

        return null;
    }
}
