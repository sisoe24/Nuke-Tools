import { assert } from "console";
import * as vscode from "vscode";
import { _commands } from "../../extension";

const config = vscode.workspace.getConfiguration("nukeTools");

const _package = vscode.extensions.getExtension(
    "virgilsisoe.nuke-tools"
)!.packageJSON;

// const configuration = _package["contributes"]["configuration"][0]["properties"];

suite.skip("Package names", () => {
    test("Check activation events commands name", () => {
        for (const command of _package["activationEvents"]) {
            assert(
                Object.values(_commands).includes(command["command"]),
                `Missing command from package.json: ${command["command"]}`
            );
        }
    });
    test("Check that commands name", () => {
        for (const command of _package["contributes"]["commands"]) {
            assert(
                Object.values(_commands).includes(command["command"]),
                `Missing command from package.json: ${command["command"]}`
            );
        }
    });
});

// suite.skip("Options", () => {
//     test("Check if valid executable returns an ExecutablePath object", () => {
//         const path = executables.getExecutable("primaryExecutablePath");
//         assert.strictEqual(path.constructor, executables.ExecutablePath);
//     });
//     test("Get executable from configuration", () => {
//         assert.throws(() => {
//             executables.getExecutable("noExecutablePath");
//         }, Error);
//     });
//     test("Get option from configuration", () => {
//         const shouldRestart = config.get(
//             "nukeExecutable.options.restartInstance"
//         );
//         assert.strictEqual(typeof shouldRestart, "boolean");
//     });
// });
//# sourceMappingURL=configuration_names.test.js.map
