import * as vscode from "vscode";

export type FormatterFunction = (text: string, tabSize: number) => string;

/**
 * Enhanced BlinkScript formatting provider.
 */
export class ScriptFormattingProvider implements vscode.DocumentFormattingEditProvider {
    private formatter: FormatterFunction;

    constructor(formatter: FormatterFunction) {
        this.formatter = formatter;
    }

    /**
     * Provide document formatting edits.
     *
     * @param document vscode document to analyze
     * @param options vscode formatting options
     * @returns an array with the provider result
     */
    public provideDocumentFormattingEdits(
        document: vscode.TextDocument,
        options: vscode.FormattingOptions
    ): vscode.ProviderResult<vscode.TextEdit[]> {
        const tabSize = options.tabSize || 2;
        const text = this.formatter(document.getText(), tabSize);

        const fullRange = new vscode.Range(
            0,
            0,
            document.lineCount - 1,
            document.lineAt(document.lineCount - 1).text.length
        );

        return [vscode.TextEdit.replace(fullRange, text)];
    }
}

export function registerFormatterProvider(
    context: vscode.ExtensionContext,
    selector: vscode.DocumentSelector,
    formatter: FormatterFunction
): string {
    const provider = new ScriptFormattingProvider(formatter);

    context.subscriptions.push(
        vscode.languages.registerDocumentFormattingEditProvider(selector, provider)
    );
    return "abc";
}
