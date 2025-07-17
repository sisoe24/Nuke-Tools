/**
 * Apply proper indentation to BlinkScript code.
 *
 * Uses standard brace-based indentation for most code,
 * but adds special handling for param: and local: sections within kernels.
 *
 * @param text text to format
 * @param tabSize number of spaces for indentation
 * @returns formatted text
 */
function applyIndentation(text: string, tabSize = 2): string {
    const indentString = " ".repeat(tabSize);

    let indentLevel = 0;
    let nodeIndentLevel = 0;
    let inComplexData = false;

    const lines = text.split("\n");
    const formattedLines = lines.map((line) => {
        const trimmed = line.trim();

        // Skip empty lines
        if (!trimmed) {
            return "";
        }

        // Check if this is a node declaration (starts with uppercase letter and has opening brace)
        const nodePattern = /^[A-Z]\w*\s*\{/;
        if (nodePattern.test(trimmed)) {
            // This is a node declaration - reset everything
            indentLevel = 0;
            nodeIndentLevel = 1;
            inComplexData = false;
            return trimmed;
        }

        // Handle closing braces that close the entire node
        if (trimmed === "}" && indentLevel <= nodeIndentLevel && !inComplexData) {
            indentLevel = 0;
            nodeIndentLevel = 0;
            return trimmed;
        }

        // Check for complex data structures (like curves, toolbox)
        const complexDataPattern = /^(curves|toolbox)\s*\{/;
        if (complexDataPattern.test(trimmed)) {
            inComplexData = true;
            return indentString.repeat(nodeIndentLevel) + trimmed;
        }

        // If we're in complex data, just preserve the original indentation relative to the node
        if (inComplexData) {
            // Check if this line closes the complex data structure
            if (trimmed === "}" && line.indexOf("}") === line.lastIndexOf("}")) {
                inComplexData = false;
                return indentString.repeat(nodeIndentLevel) + trimmed;
            }
            // For complex data content, preserve original spacing but add node-level indent
            const originalSpacing = line.match(/^\s*/)?.[0] || "";
            return indentString.repeat(nodeIndentLevel) + originalSpacing + trimmed;
        }

        // Handle simple properties inside nodes
        if (nodeIndentLevel > 0) {
            // Simple property lines
            if (!trimmed.includes("{") && !trimmed.includes("}")) {
                return indentString.repeat(nodeIndentLevel) + trimmed;
            }

            // Handle simple nested structures (like addUserKnob)
            if (trimmed.endsWith("{")) {
                const result = indentString.repeat(nodeIndentLevel) + trimmed;
                indentLevel = nodeIndentLevel + 1;
                return result;
            }

            if (trimmed === "}") {
                indentLevel = nodeIndentLevel;
                return indentString.repeat(nodeIndentLevel) + trimmed;
            }

            // Content inside simple nested structures
            if (indentLevel > nodeIndentLevel) {
                return indentString.repeat(indentLevel) + trimmed;
            }
        }

        // Regular line inside a node
        return indentString.repeat(Math.max(nodeIndentLevel, indentLevel)) + trimmed;
    });

    return formattedLines.join("\n");
}

/**
 * Format Nuke script file
 *
 * @param text text to format
 * @param tabSize number of spaces for indentation
 * @returns formatted text
 */
export function nukeScriptFormatter(text: string, tabSize = 2): string {
    return applyIndentation(text, tabSize);
}
