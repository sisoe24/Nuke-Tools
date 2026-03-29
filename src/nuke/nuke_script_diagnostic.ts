import * as vscode from "vscode";
import { DiagnosticResult } from "../providers/diagnostic";

/**
 * Nuke script validator function.
 */
export function nukeValidator(document: vscode.TextDocument): DiagnosticResult[] {
    const diagnostics: DiagnosticResult[] = [];

    const setVariables = new Map<string, { line: number; start: number; end: number }>();
    const usedVariables = new Map<string, Array<{ line: number; column: number }>>();

    let braceBalance = 0;
    const openBraces: Array<{ line: number; column: number }> = [];

    const text = document.getText();
    const lines = text.split("\n");

    // parse document
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmedLine = line.trim();

        // Skip comments and empty lines
        if (
            trimmedLine.startsWith("//") ||
            trimmedLine.startsWith("#") ||
            trimmedLine.length === 0
        ) {
            continue;
        }

        // Check for set variable declarations
        const setMatch = line.match(/set\s(\w+)\s\[stack \d\]/);
        if (setMatch) {
            const varName = setMatch[1];
            setVariables.set(varName, {
                line: i,
                start: setMatch.index ?? 0,
                end: setMatch.input?.length ?? line.length,
            });
        }

        // Check for $variable usage. We expect a line could have multiple variables
        const variableRegex = /\$(\w+)/g;
        let match;
        while ((match = variableRegex.exec(line)) !== null) {
            const varName = match[1];
            const varIndex = match.index;

            let locations = usedVariables.get(varName);
            if (!locations) {
                locations = [];
                usedVariables.set(varName, locations);
            }
            locations.push({ line: i, column: varIndex });
        }

        // Track braces
        for (let j = 0; j < line.length; j++) {
            if (line[j] === "{") {
                braceBalance++;
                openBraces.push({ line: i, column: j });
            } else if (line[j] === "}") {
                braceBalance--;
                if (openBraces.length > 0) {
                    openBraces.pop();
                }
                if (braceBalance < 0) {
                    diagnostics.push({
                        range: new vscode.Range(i, j, i, j + 1),
                        message: "Unexpected closing brace - no matching opening brace",
                        severity: vscode.DiagnosticSeverity.Error,
                        code: "unmatched-closing-brace",
                        source: "nuke-script",
                    });
                    braceBalance = 0;
                }
            }
        }
    }

    // Mark unused set variables
    for (const [varName, location] of setVariables) {
        if (!usedVariables.has(varName)) {
            diagnostics.push({
                range: new vscode.Range(location.line, location.start, location.line, location.end),
                message: `Variable '${varName}' is set but never used.`,
                severity: vscode.DiagnosticSeverity.Error,
                code: "unused-set-variable",
                source: "nuke-script",
            });
        }
    }

    // Mark undefined variables
    for (const [varName, usageLocations] of usedVariables) {
        if (setVariables.has(varName)) {
            continue;
        }

        for (const location of usageLocations) {
            diagnostics.push({
                range: new vscode.Range(
                    location.line,
                    location.column,
                    location.line,
                    location.column + varName.length + 1
                ),
                message: `Variable '${varName}' is used but never set.`,
                severity: vscode.DiagnosticSeverity.Error,
                code: "undefined-variable",
                source: "nuke-script",
            });
        }
    }

    // Mark unterminated braces
    for (const brace of openBraces) {
        diagnostics.push({
            range: new vscode.Range(brace.line, brace.column, brace.line, brace.column + 1),
            message: "Unterminated opening brace - missing closing brace",
            severity: vscode.DiagnosticSeverity.Error,
            code: "unterminated-brace",
            source: "nuke-script",
        });
    }

    return diagnostics;
}
