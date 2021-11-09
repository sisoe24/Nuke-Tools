import * as assert from "assert";
import * as utils from "../../utils";

suite("NukeToolsConfig", () => {
    test("Get a string valid configuration", () => {
        assert.strictEqual(
            typeof utils.nukeToolsConfig("nukeExecutable.primaryExecutablePath"),
            "string"
        );
    });

    test("Get a boolean valid configuration", () => {
        assert.strictEqual(typeof utils.nukeToolsConfig("network.debug"), "boolean");
    });

    test("Get invalid configuration", () => {
        assert.throws(() => {
            utils.nukeToolsConfig("maya");
        }, Error);
    });

    // TODO: dont know how to get vscode context.
    test.skip("Update message");
});

// XXX: test extension.ts?
