import * as assert from "assert";
import * as utils from "../../utils";

suite("NukeToolsConfig", () => {
    test("Get valid value", () => {
        assert.ok(utils.nukeToolsConfig("network.debug"));
    });

    test("Get invalid value", () => {
        assert.throws(() => {
            utils.nukeToolsConfig("maya");
        }, Error);
    });

    // TODO: dont know how to get vscode context.
    test.skip("Update message");
});

// XXX: test extension.ts?
