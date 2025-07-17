import * as vscode from "vscode";

/**
 * Diagnostic result from a validator function.
 */
export interface DiagnosticResult {
    range: vscode.Range;
    message: string;
    severity: vscode.DiagnosticSeverity;
    code: string;
    source: string;
}

/**
 * Validator function signature.
 */
export type ValidatorFunction = (document: vscode.TextDocument) => DiagnosticResult[];

/**
 * Generic diagnostic provider that accepts validator functions.
 */
export class GenericDiagnosticProvider {
    private diagnosticCollection: vscode.DiagnosticCollection;
    private validator: ValidatorFunction;

    constructor(languageId: string, validator: ValidatorFunction) {
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection(languageId);
        this.validator = validator;
    }

    /**
     * Validate a document using the injected validator function.
     */
    public validateDocument(document: vscode.TextDocument): void {
        const diagnosticResults = this.validator(document);

        const diagnostics = diagnosticResults.map((result) => {
            const diagnostic = new vscode.Diagnostic(result.range, result.message, result.severity);
            diagnostic.source = result.source;
            diagnostic.code = result.code;
            return diagnostic;
        });

        this.diagnosticCollection.set(document.uri, diagnostics);
    }

    /**
     * Clear diagnostics for a document.
     */
    public clearDiagnostics(document: vscode.TextDocument): void {
        this.diagnosticCollection.delete(document.uri);
    }

    /**
     * Clear all diagnostics.
     */
    public clearAllDiagnostics(): void {
        this.diagnosticCollection.clear();
    }

    /**
     * Dispose of the diagnostic collection.
     */
    public dispose(): void {
        this.diagnosticCollection.dispose();
    }
}

/**
 * Register a generic diagnostic provider with VS Code.
 */
export function registerGenericDiagnosticProvider(
    context: vscode.ExtensionContext,
    languageId: string,
    validator: ValidatorFunction
): GenericDiagnosticProvider {
    const provider = new GenericDiagnosticProvider(languageId, validator);

    // Validate documents when they are opened
    const onOpenDisposable = vscode.workspace.onDidOpenTextDocument((document) => {
        if (document.languageId === languageId) {
            provider.validateDocument(document);
        }
    });

    // Validate documents when they are saved
    const onSaveDisposable = vscode.workspace.onDidSaveTextDocument((document) => {
        if (document.languageId === languageId) {
            provider.validateDocument(document);
        }
    });

    // Clear diagnostics when documents are closed
    const onCloseDisposable = vscode.workspace.onDidCloseTextDocument((document) => {
        if (document.languageId === languageId) {
            provider.clearDiagnostics(document);
        }
    });

    // Add to context subscriptions for cleanup
    context.subscriptions.push(provider, onOpenDisposable, onSaveDisposable, onCloseDisposable);

    // Validate all currently open documents
    vscode.workspace.textDocuments.forEach((document) => {
        if (document.languageId === languageId) {
            provider.validateDocument(document);
        }
    });

    return provider;
}
