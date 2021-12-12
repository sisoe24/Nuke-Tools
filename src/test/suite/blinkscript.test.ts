import * as assert from "assert";
import * as testUtils from "./test_utils";

import * as blinkFormat from "../../blinkscript/blink_format";
import * as blinkSnippet from "../../blinkscript/blink_snippet";
import * as blinkCompletion from "../../blinkscript/blink_completion";

import * as vscode from "vscode";

/**
 * File content to write at the beginning of the test.
 */
const fileContent = `
int main()
{
       
     
    int n =   5;
   
  
    return 0;
}`.trim();

const formattedFile = `
int main() {

    int n = 5;

    return 0;
}`.trim();

const demoFile = "blinkscript_demo.py";

suite("BlinkScript", () => {
    suiteSetup("Open demo file", async () => {
        await testUtils.createDemoContent(demoFile, fileContent);
    });

    test("Formatting", async () => {
        const editor = await testUtils.focusDemoFile(demoFile, 1);

        const formatter = new blinkFormat.BlinkScriptFormat();
        const provider = await formatter.provideDocumentFormattingEdits(editor.document);
        if (provider) {
            assert.strictEqual(provider[0]["newText"], formattedFile);
        }
    });

    test("Snippet", async () => {
        const snippets = new blinkSnippet.BlinkSnippets();
        const provider = snippets.provideCompletionItems();

        if (provider) {
            assert.strictEqual(provider[0].label, "kernel");
            assert.strictEqual(provider[0].documentation, "Saturation sample script.");
            if (provider[0].insertText) {
                const snippetText = provider[0].insertText as vscode.SnippetString;
                assert.strictEqual(snippetText.value, blinkSnippet.saturationTemplate);
            }
        }
    });
});

const codeSuggestionContent = `
kernel Sample : ImageComputationKernel<ePixelWise> {
    Image<eRead>
}
`.trim();

const codeSuggestionDemoFile = "code_suggestion.blink";

suite("BlinkScript Code Suggestion", () => {
    suiteSetup("Open demo file", async () => {
        await testUtils.createDemoContent(codeSuggestionDemoFile, codeSuggestionContent);
    });

    test("Invalid completion items", () => {
        assert.throws(() => {
            blinkCompletion.getCompletions("invalid items");
        }, Error);
    });

    test("No provider", async () => {
        const editor = await testUtils.focusDemoFile(demoFile, 1);

        const completion = new blinkCompletion.BlinkScriptCompletionProvider();
        const provider = completion.provideCompletionItems(
            editor.document,
            new vscode.Position(0, 0)
        );

        assert.ok(!provider);
    });

    test("kernelType items", async () => {
        const editor = await testUtils.focusDemoFile(codeSuggestionDemoFile, 1);

        const completion = new blinkCompletion.BlinkScriptCompletionProvider();
        const provider = completion.provideCompletionItems(
            editor.document,
            new vscode.Position(0, 17)
        );

        const kernelType = blinkCompletion.completionFile.kernelTypes;

        if (provider) {
            for (const item of provider) {
                assert.ok(Object.prototype.hasOwnProperty.call(kernelType, item.label as string));
            }
        }
    });

    test("kernelGranularity items", async () => {
        const editor = await testUtils.focusDemoFile(codeSuggestionDemoFile, 1);

        const completion = new blinkCompletion.BlinkScriptCompletionProvider();
        const provider = completion.provideCompletionItems(
            editor.document,
            new vscode.Position(0, 42)
        );

        const kernelType = blinkCompletion.completionFile.kernelGranularity;

        if (provider) {
            for (const item of provider) {
                assert.ok(Object.prototype.hasOwnProperty.call(kernelType, item.label as string));
            }
        }
    });

    test("imageAccess items", async () => {
        const editor = await testUtils.focusDemoFile(codeSuggestionDemoFile, 1);

        const completion = new blinkCompletion.BlinkScriptCompletionProvider();
        const provider = completion.provideCompletionItems(
            editor.document,
            new vscode.Position(1, 12)
        );

        const kernelType = blinkCompletion.completionFile.imageAccess;

        if (provider) {
            for (const item of provider) {
                assert.ok(Object.prototype.hasOwnProperty.call(kernelType, item.label as string));
            }
        }
    });
});
