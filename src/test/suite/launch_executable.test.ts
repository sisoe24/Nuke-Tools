import * as vscode from "vscode";
import { setTimeout } from "timers";

import * as assert from "assert";
import * as executables from "../../launch-executable";

const config = vscode.workspace.getConfiguration("nukeTools");

suite("ExecutablePath()", () => {
    const path = "path/app name/bin";

    test("quotePath()", () => {
        const execPath = new executables.ExecutablePath(path);
        const quotedPath = execPath.quotePath(path);
        assert.strictEqual(quotedPath, `"${path}"`);
    });

    test.skip("Check path if on Windows", () => {
        // TODO: monkey path the os module?
        it("should insert he & operator if on Windows system");
    });

    test("basename()", () => {
        // TODO: monkey path the os module?
        const execPath = new executables.ExecutablePath(path);
        const basename = execPath.basename();
        assert.strictEqual(basename, "bin");
    });

    test("isValid()", () => {
        const home = require("os").homedir();
        const paths = { "fake/path/bin": false, home: true };

        Object.entries(paths).forEach(([path, exists]) => {
            const execPath = new executables.ExecutablePath(path);
            assert.strictEqual(execPath.isValid(), exists);
        });
    });

    test("cliCmd()", () => {
        const execPath = new executables.ExecutablePath(path);
        const cmd = execPath.cliCmd();
        assert.strictEqual(cmd, `"${path}"`);
    });

    test("CLI cmd with arguments", () => {
        const execPath = new executables.ExecutablePath(path);
        execPath.args = "-random --args";

        assert.match(execPath.cliCmd(), /&?\s?".+?" -random --args/g);
    });
});

/**
 * Some tests will need to wait for vscode to register the actions. An example will
 * be creating/killing terminals and configuration update.
 *
 * @param milliseconds - time to sleep
 * @returns
 */
const sleep = (milliseconds: number) => {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
};

suite("Terminal instance", () => {
    const terminalName = "test";
    const sleepTime = 200;

    test("Terminal was created", () => {
        const execPath = new executables.ExecutablePath("path/to/bin.app");
        executables.execCommand(execPath);

        let match = false;
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name === "bin.app") {
                match = true;
            }
        });

        assert.ok(match);
    });

    // TODO: currently don't know how to grab this info
    test.skip("Check if terminal has cmd line text", () => {});
    test.skip("Check if terminal is shown", () => {});

    test("Restart terminal instance", async () => {
        vscode.window.createTerminal(terminalName);
        executables.restartInstance(terminalName);
        vscode.window.createTerminal(terminalName);

        await sleep(sleepTime);

        let terminalInstances = 0;
        vscode.window.terminals.forEach((terminal) => {
            if (terminal.name === terminalName) {
                terminalInstances += 1;
            }
        });
        assert.strictEqual(terminalInstances, 1);
    });

    test("Create multiple terminal instances", async () => {
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
        await sleep(sleepTime);
    });
});

async function changeConfig(section: string, settings: any) {
    await config.update(
        section,
        settings,
        vscode.ConfigurationTarget.Workspace
    );
}



suite.skip("Arguments", () => {
    test("Optional arguments", async () => {});
    test("Default arguments", async () => {
        let result = await Promise.resolve(
            changeConfig(
                "nukeExecutable.options.defaultCommandLineArguments",
                "random args x"
            )
        );

        const resolve = (args: any) => {
            console.log(" resolve ~ args", args);
        };

        const reject = (args: any) => {
            console.log(" reject ~ args", args);
        };

        console.log("what 1");
        changeConfig(
            "nukeExecutable.options.defaultCommandLineArguments",
            "random args"
        ).then(
            () => {
                const path = executables.appendArgs("fake/path");
                console.log("line 70 ~ path", path);
                assert.strictEqual(path, "fake/path LOL");
            },
            () => {
                console.log("what 3");
                reject("bo");
            }
        );
        console.log("what 2");
        // const config = vscode.workspace.getConfiguration(`nukeTools`);
        // config.update(
        //     "nukeExecutable.options.defaultCommandLineArguments",
        //     "LOLx",
        //     vscode.ConfigurationTarget.Workspace
        // );
    });
});
