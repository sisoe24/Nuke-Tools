import * as vscode from "vscode";
import * as utils from "./test_utils";
import * as assert from "assert";
import { join } from "path";
import * as executables from "../../launch_executable";

/**
 * Path to an executable bash file named: myapp.
 */
const samplePath = join(utils.demoPath, "path with space", "nuke");

suite("ExecutablePath()", () => {
    test("quotePath()", () => {
        const execPath = new executables.ExecutablePath(samplePath, "suffix");
        const quotedPath = execPath.quotePath(samplePath);
        assert.strictEqual(quotedPath, `"${samplePath}"`);
    });

    test.skip("Check path if on Windows", () => {
        // TODO: can monkeypatch the os module?
        it("should insert he & operator if on Windows system");
    });

    test("basename()", () => {
        const execPath = new executables.ExecutablePath(samplePath, "suffix");
        const basename = execPath.basename();
        assert.strictEqual(basename, "nuke");
    });

    test("Path should be invalid.", () => {
        const execPath = new executables.ExecutablePath("fake/path/bin", "suffix");
        assert.strictEqual(execPath.isValid(), false);
    });

    test("Path should be valid.", () => {
        const execPath = new executables.ExecutablePath(samplePath, "suffix");
        assert.strictEqual(execPath.isValid(), true);
    });

    test("cliCmd()", () => {
        const execPath = new executables.ExecutablePath(samplePath, "suffix");
        const cmd = execPath.cliCmd();
        assert.strictEqual(cmd, `"${samplePath}"`);
    });

    test("CLI cmd with arguments", () => {
        const execPath = new executables.ExecutablePath(samplePath, "suffix");
        execPath.args = "-fake --args";

        const pattern = new RegExp(`&?\\s?"${samplePath}" -fake --args`);
        assert.match(execPath.cliCmd(), pattern);
    });
});

const sleepTime = 400;

suite("Launch executable", () => {
    suiteSetup("Setup Clean settings file", () => {
        utils.cleanSettings();
    });

    teardown("Tear Down settings file", () => {
        utils.cleanSettings();
    });

    test("Primary executable with no arguments", async () => {
        await utils.updateConfig("nukeExecutable.primaryExecutablePath", samplePath);

        const execPath = executables.launchPrimaryExecutable();
        const pattern = new RegExp(`&?\\s?"${samplePath}"`);

        assert.match(execPath.cliCmd(), pattern);
    });

    test("Primary executable with Default arguments", async () => {
        await utils.updateConfig("nukeExecutable.primaryExecutablePath", samplePath);

        await utils.updateConfig(
            "nukeExecutable.options.defaultCommandLineArguments",
            "-fake --args"
        );

        const execPath = executables.launchPrimaryExecutable();

        const pattern = new RegExp(`&?\\s?"${samplePath}" -fake --args`);
        assert.match(execPath.cliCmd(), pattern);
    });

    test("Alternative executable with Default arguments", async () => {
        await utils.updateConfig(
            "nukeExecutable.options.defaultCommandLineArguments",
            "-fake --args"
        );

        await utils.updateConfig("nukeExecutable.secondaryExecutablePath", samplePath);

        const execPath = executables.launchSecondaryExecutable();

        const pattern = new RegExp(`&?\\s?"${samplePath}" -fake --args`);
        assert.match(execPath.cliCmd(), pattern);
    });

    test.skip("Primary executable with prompt arguments", async () => {
        // XXX: this will sto test execution waiting for user input
        await utils.updateConfig("nukeExecutable.primaryExecutablePath", samplePath);

        const execPath = await executables.launchPromptExecutable();

        const pattern = new RegExp(`&?\\s?"${samplePath}" ok`);
        assert.match(execPath.cliCmd(), pattern);
    });
});

suite("Terminal instance", () => {
    const terminalName = "test";

    test("Terminal was created", () => {
        const execPath = new executables.ExecutablePath("path/to/bin.app", "suffix");
        executables.execCommand(execPath);

        let match = false;
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name === "bin.app suffix") {
                match = true;
            }
        });

        assert.ok(match);
    });

    // TODO: currently don't know how to grab this info
    test.skip("Check if terminal has cmd line text");
    test.skip("Check if terminal is shown");

    test("Restart terminal instance", async () => {
        vscode.window.createTerminal(terminalName);
        executables.restartInstance(terminalName);
        vscode.window.createTerminal(terminalName);

        await utils.sleep(200);

        let terminalInstances = 0;
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name === terminalName) {
                terminalInstances += 1;
            }
        });
        assert.strictEqual(terminalInstances, 1);
    });

    test("Create multiple terminal instances", () => {
        vscode.window.createTerminal(terminalName);
        vscode.window.createTerminal(terminalName);

        let terminalInstances = 0;
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name === terminalName) {
                terminalInstances += 1;
            }
        });
        assert.strictEqual(terminalInstances, 2);
    });

    teardown("Kill terminals after tests", async () => {
        vscode.window.terminals.forEach((terminal) => {
            terminal.dispose();
        });
        await utils.sleep(sleepTime);
    });
});
