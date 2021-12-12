import * as vscode from "vscode";

/**
 * Clean empty lines.
 *
 * @param text text to format
 * @returns formatted text
 */
export function cleanEmptyLines(text: string): string {
    return text.replace(/^\s+$/gm, "");
}

/**
 * Clean multiple spaces.
 *
 * @param text text to format
 * @returns formatted text
 */
export function cleanMultiSpace(text: string): string {
    return text.replace(/(?<=[^ \n]) {2,}/gm, " ");
}

/**
 * Un-indent bracket.
 *
 * `if ()`
 *
 * `{`
 *
 * to
 *
 * `if () {`
 *
 * @param text text to format
 * @returns formatted text
 */
export function unindentBlock(text: string): string {
    return text.replace(/\s*{/gm, " {");
}

/**
 * Format BlinkScript file.
 *
 * @param text text to format
 * @returns formatted text
 */
export function formatFile(text: string): string {
    text = cleanEmptyLines(text);
    text = cleanMultiSpace(text);
    text = unindentBlock(text);
    return text;
}

export class BlinkScriptFormat implements vscode.DocumentFormattingEditProvider {
    public provideDocumentFormattingEdits(
        document: vscode.TextDocument
    ): vscode.ProviderResult<vscode.TextEdit[]> {
        const lines = document.lineCount;
        const text = formatFile(document.getText());

        return [vscode.TextEdit.replace(new vscode.Range(0, 0, lines - 1, 0), text)];
    }
}
