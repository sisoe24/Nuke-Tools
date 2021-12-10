import * as vscode from "vscode";

export function createCompletions(
    object: { [s: string]: string } | ArrayLike<string>
): vscode.CompletionItem[] {
    const completionArray: vscode.CompletionItem[] = [];
    for (const [key, value] of Object.entries(object)) {
        const item = new vscode.CompletionItem(key, vscode.CompletionItemKind.Property);
        item.detail = value;
        completionArray.push(item);
    }
    return completionArray;
}

export class BlinkScriptCompletionProvider implements vscode.CompletionItemProvider {
    provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): vscode.ProviderResult<
        vscode.CompletionItem[] | vscode.CompletionList<vscode.CompletionItem>
    > {
        const linePrefix = document.lineAt(position).text.substr(0, position.character);

        if (linePrefix.match(/kernel\s\w+\s*:\s*\w+(?!<)$/)) {
            const kernelsType = {
                ImageComputationKernel: `Used for image processing, this takes zero or more 
                    images as input and produces one or more images as output`,
                ImageRollingKernel: `Used for image processing, where there is a data 
                    dependency between the output at different points in the output space.
                    With an ImageComputationKernel, there are no guarantees about the
                    order in which the output pixels will be filled in. With an ImageRollingKernel,
                    you can choose to "roll" the kernel either horizontally or vertically over the iteration bounds,
                    allowing you to carry data along rows or down columns respectively`,
                ImageReductionKernel: `Used to "reduce" an image down to a value or set of 
                    values that represent it, for example to calculate statistics such 
                    as the mean or variance of an image`,
            };

            return createCompletions(kernelsType);
        } else if (linePrefix.match(/kernel\s\w+\s*:\s*\w+\s*</)) {
            const kernelGranularity = {
                ePixelWise: `At each pixel, a pixel wise kernel can write to all
                the channels in the output and can access any channel in the input. 
                You would use a pixelwise kernel for any operation where there is 
                interdependence between the channels, for example a saturation`,
                eComponentWise: `Component wise processing means that each channel 
                in the output image will be processed independently. When processing 
                each channel, only values from the corresponding channel in the input(s) can be accessed`,
            };

            return createCompletions(kernelGranularity);
        } else if (linePrefix.match(/Image</)) {
            const imageType = {
                eEdgeClamped: ``,
                eEdgeConstant: ``,
                eAccessPoint: ``,
                eAccessRanged1D: ``,
                eAccessRanged2D: ``,
                eAccessRangedRandom: ``,
                eRead: ``,
                eWrite: ``,
                eReadWrite: ``,
            };

            return createCompletions(imageType);
        }

        return null;
    }
}
