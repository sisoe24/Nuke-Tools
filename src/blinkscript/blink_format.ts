import * as vscode from "vscode";

/**
 * Clean empty lines.
 *
 * @param text text to format
 * @returns formatted text
 */
export function cleanEmptyLines(text: string): string {
    return text.replace(/^\s+\n$/gm, "\n");
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
 * Format inline else statements.
 *
 * Moves `else if` and `else` to the same line as the closing brace.
 * This should be called AFTER indentation is applied.
 *
 * @param text text to format
 * @returns formatted text
 */
export function formatInlineElse(text: string): string {
    // Handle } else if (condition) { - preserve the indentation of the else block
    text = text.replace(/^(\s*)\}\s*\n\s*else\s+if\s*\(/gm, "$1} else if (");

    // Handle } else { - preserve the indentation of the else block
    text = text.replace(/^(\s*)\}\s*\n\s*else\s*\{/gm, "$1} else {");

    return text;
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
 * Apply proper indentation to BlinkScript code.
 *
 * Uses standard brace-based indentation for most code,
 * but adds special handling for param: and local: sections within kernels.
 *
 * @param text text to format
 * @param tabSize number of spaces for indentation
 * @param insertSpaces use spaces instead of tabs
 * @returns formatted text
 */
export function applyIndentation(text: string, tabSize = 2, insertSpaces = true): string {
    const lines = text.split("\n");
    const indentString = insertSpaces ? " ".repeat(tabSize) : "\t";
    let indentLevel = 0;
    let inParamOrLocal = false;

    const formattedLines = lines.map((line) => {
        const trimmed = line.trim();

        // Skip empty lines
        if (!trimmed) {
            return "";
        }

        // Handle preprocessor directives (no indentation)
        if (trimmed.startsWith("#")) {
            return trimmed;
        }

        // Handle closing braces - decrease indent first
        if (trimmed.startsWith("}")) {
            indentLevel = Math.max(0, indentLevel - 1);
            inParamOrLocal = false; // Exit param/local when we close any brace
        }

        // Check if this is param: or local: section
        if (trimmed === "param:" || trimmed === "local:") {
            inParamOrLocal = true;
            return indentString.repeat(indentLevel) + trimmed;
        }

        // Check if we're exiting param/local section (function definition or other section)
        if (inParamOrLocal && (trimmed.match(/^\w+\s+\w+\s*\(/) || trimmed.endsWith(":"))) {
            inParamOrLocal = false;
        }

        // Calculate base indentation
        let currentIndent = indentLevel;

        // Add extra indent if we're in param/local section and it's not a function/section
        if (inParamOrLocal &&
            !trimmed.startsWith("}") &&
            !trimmed.match(/^\w+\s+\w+\s*\(/) &&
            !trimmed.endsWith(":")) {
            currentIndent += 1;
        }

        const result = indentString.repeat(currentIndent) + trimmed;

        // Handle opening braces - increase indent after formatting this line
        if (trimmed.endsWith("{")) {
            indentLevel++;
        }

        return result;
    });

    return formattedLines.join("\n");
}

/**
 * Format BlinkScript file with enhanced features.
 *
 * @param text text to format
 * @param tabSize number of spaces for indentation
 * @param insertSpaces use spaces instead of tabs
 * @returns formatted text
 */
export function formatFile(text: string, tabSize = 2, insertSpaces = true): string {
    // Apply basic cleaning
    text = cleanEmptyLines(text);
    text = cleanMultiSpace(text);

    // Apply bracket formatting
    text = unindentBlock(text);

    // Apply proper indentation first
    text = applyIndentation(text, tabSize, insertSpaces);

    // Format inline else statements AFTER indentation
    text = formatInlineElse(text);

    return text;
}

/**
 * Enhanced BlinkScript formatting provider.
 */
export class BlinkScriptFormat implements vscode.DocumentFormattingEditProvider {
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
        const insertSpaces = options.insertSpaces ?? true;
        const text = formatFile(document.getText(), tabSize, insertSpaces);

        const fullRange = new vscode.Range(
            0,
            0,
            document.lineCount - 1,
            document.lineAt(document.lineCount - 1).text.length
        );

        return [vscode.TextEdit.replace(fullRange, text)];
    }
}
