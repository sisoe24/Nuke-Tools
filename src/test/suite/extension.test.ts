import * as assert from "assert";
import { getConfig } from "../../config";

suite("NukeToolsConfig", () => {
    test("Get a string valid configuration", () => {
        assert.strictEqual(
            typeof getConfig("nukeExecutable.primaryExecutablePath"),
            "string"
        );
    });

    test("Get a boolean valid configuration", () => {
        assert.strictEqual(typeof getConfig("network.debug"), "boolean");
    });

    test("Get invalid configuration", () => {
        assert.throws(() => {
            getConfig("maya");
        }, Error);
    });

});
