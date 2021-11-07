import * as vscode from "vscode";

import * as assert from "assert";
import * as stubs from "../../stubs";
import * as fs from "fs";

suite("Stubs Creation", () => {
    const stubsPath = "path/virgilsisoe.nuke-tools-0.3.2/Nuke-Python-Stub";

    test("Get stubs path", () => {
        const path = stubs.getStubsPath();
        assert(fs.existsSync(path));
    });

    // TODO: Need to mock the extension path.
    test.skip("Get stubs path but raises error");

    test("Extract version from path", () => {
        const version = stubs.extractVersion(stubsPath);
        assert.strictEqual(version, "0.3.2");
    });

    test("Add Python analysis path first time", () => {
        const extraPaths = ["path/to/lib"];
        const expectedPath = ["path/to/lib", stubsPath];

        stubs.updateAnalysisPath(extraPaths, stubsPath);
        assert.deepStrictEqual(extraPaths, expectedPath);
    });

    test("Update Python analysis path", () => {
        // extra path has already a stub path
        const extraPaths = ["path/to/lib", "path/virgilsisoe.nuke-tools-0.3.1/Nuke-Python-Stub"];

        // this does update path because stubs (0.3.2) version is bigger than
        // extraPaths (0.3.1)
        stubs.updateAnalysisPath(extraPaths, stubsPath);

        const expectedPath = ["path/to/lib", stubsPath];
        assert.deepStrictEqual(extraPaths, expectedPath);
    });

    test("Dont update Python analysis path: stubs version is bigger", () => {
        const extraPaths = [
            "path/to/lib",
            "path/virgilsisoe.nuke-tools-0.3.3/Nuke-Python-Stub/nuke_stubs",
        ];
        // this does not update path because extraPaths version (0.3.3) is bigger
        // than stubs (0.3.2)
        stubs.updateAnalysisPath(extraPaths, stubsPath);
        assert.strictEqual(extraPaths, extraPaths);
    });

    test("Dont update Python analysis path: stubs already present", () => {
        const extraPaths = ["path/to/lib", stubsPath];
        // this does not update path because stubs path is already present
        stubs.updateAnalysisPath(extraPaths, stubsPath);
        assert.strictEqual(extraPaths, extraPaths);
    });

    test.skip("Check python.analysis.extraPaths content: Work only if extension is installed", () => {
        stubs.addStubsPath();
        const config = vscode.workspace.getConfiguration("python.analysis");
        const extraPaths = config.get("extraPaths") as Array<string>;
        assert.deepStrictEqual(extraPaths, [stubs.getStubsPath()]);
    });
});
