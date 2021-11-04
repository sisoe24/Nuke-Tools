import * as update from "../../update_message";

import * as assert from "assert";

suite("Version", () => {
    test("Not a valid constructor", () => {
        for (const constructor of [undefined, "some version"]) {
            const version = new update.Version(constructor);
            assert.deepStrictEqual(version.toStr, "0.0.0");
            assert.deepStrictEqual(version.version, [0, 0, 0]);
        }
    });

    test("Numeric version", () => {
        const version = new update.Version("0.3.7");
        assert.deepStrictEqual(version.version, [0, 3, 7]);
    });

    test("String version", () => {
        const version = new update.Version("0.3.7");
        assert.strictEqual(version.toStr, "0.3.7");
    });

    test("Major", () => {
        const version = new update.Version("1.3.0");
        assert.strictEqual(version.major(), 1);
    });

    test("Minor", () => {
        const version = new update.Version("0.3.0");
        assert.strictEqual(version.minor(), 3);
    });

    test("Patch", () => {
        const version = new update.Version("0.3.7");
        assert.strictEqual(version.patch(), 7);
    });

    test("Should be isBiggerThan (no patch)", () => {
        const otherVersion = new update.Version("0.2.0");

        for (const ver of ["1.0.0", "0.3.0"]) {
            const version = new update.Version(ver);
            assert.ok(version.isBiggerThan(otherVersion, false));
        }
    });

    test("Should NOT be isBiggerThan (no patch)", () => {
        const otherVersion = new update.Version("0.2.0");

        for (const ver of ["0.2.7", "0.2.0", "0.1.0"]) {
            const version = new update.Version(ver);
            assert.ok(!version.isBiggerThan(otherVersion, false));
        }
    });

    test("Should be isBiggerThan (with patch)", () => {
        const otherVersion = new update.Version("0.2.0");
        const version = new update.Version("0.2.1");
        assert.ok(version.isBiggerThan(otherVersion, true));
    });
});
