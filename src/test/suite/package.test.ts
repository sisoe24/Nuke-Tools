import * as assert from "assert";

import * as utils from "../../utils";
import * as vscode from "vscode";

/**
 * TODO:
 *
 * 1. Check that contributes.commands are inside the activation events list.
 * this will also check for wrong names.
 *
 * 2. Check that all contributes.commands are called in extension.ts
 * this will also check for wrong names.
 *
 * 3. Check configuration.properties default value types.
 *
 * 4. Check configuration.properties names inside various src files to check if
 * names are not misspelled.
 *
 * 5. Check menus properties: if name matches command and when condition.
 */

const extPackage = vscode.extensions.getExtension(
    "virgilsisoe.nuke-tools"
)!.packageJSON;
const configuration =
    extPackage["contributes"]["configuration"][0]["properties"];
console.log(configuration);
const n = {
    "nukeTools.nukeExecutable.primaryExecutablePath": "string",
    "nukeTools.nukeExecutable.secondaryExecutablePath": "string",
    "nukeTools.nukeExecutable.options.defaultCommandLineArguments": "string",
    "nukeTools.nukeExecutable.options.restartInstance": "boolean",
    "nukeTools.other.autoAddStubsPath": "boolean",
    "nukeTools.other.clearPreviousOutput": "boolean",
    "nukeTools.network.enableManualConnection": "boolean",
    "nukeTools.network.port": "string",
    "nukeTools.network.host": "string",
};
suite.only("Configuration properties", () => {
    test("Default values", () => {
        for (const [key, value] of Object.entries(configuration)) {
            console.log(key, value);
            const k: string = key;

            assert.ok(n[key as keyof typeof n] === n[value["type"]]);
        }
    });
});

// const config = vscode.workspace.getConfiguration("nukeTools");

// // TODO: test package configuration names and types

// suite.only("Get Configuration options", () => {
//     test("Check sub boolean configuration type", () => {
//         const subConfig = utils.nukeToolsConfig("other.clearPreviousOutput");
//         assert.strictEqual(typeof subConfig, "boolean");
//     });

//     test("Check sub string configuration type", () => {
//         const subConfig = utils.nukeToolsConfig("network.port");
//         assert.strictEqual(typeof subConfig, "string");
//     });

//     test("Undefined configuration", () => {
//         const subConfig = utils.nukeToolsConfig("maya");
//         assert.strictEqual(subConfig, false);
//     });
// });

// // suite.skip("Package names", () => {
// //     test("Check activation events commands name", () => {
// //         for (const command of _package["activationEvents"]) {
// //             assert(
// //                 Object.values(_commands).includes(command["command"]),
// //                 `Missing command from package.json: ${command["command"]}`
// //             );
// //         }
// //     });
// //     test("Check that commands name", () => {
// //         for (const command of _package["contributes"]["commands"]) {
// //             assert(
// //                 Object.values(_commands).includes(command["command"]),
// //                 `Missing command from package.json: ${command["command"]}`
// //             );
// //         }
// //     });

// // suite.skip("Options", () => {
// //     test("Check if valid executable returns an ExecutablePath object", () => {
// //         const path = executables.getExecutable("primaryExecutablePath");
// //         assert.strictEqual(path.constructor, executables.ExecutablePath);
// //     });
// //     test("Get executable from configuration", () => {
// //         assert.throws(() => {
// //             executables.getExecutable("noExecutablePath");
// //         }, Error);
// //     });
// //     test("Get option from configuration", () => {
// //         const shouldRestart = config.get(
// //             "nukeExecutable.options.restartInstance"
// //         );
// //         assert.strictEqual(typeof shouldRestart, "boolean");
// //     });
// // });
// //# sourceMappingURL=configuration_names.test.js.map
