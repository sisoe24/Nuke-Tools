import * as vscode from "vscode";

import * as assert from "assert";
import * as socket from "../../socket";
import { writeFileSync, existsSync, readFileSync } from "fs";
import * as path from "path";
import * as os from "os";

const cwd = vscode.extensions.getExtension(
    "virgilsisoe.nuke-tools"
)!.extensionPath;
const tmpFolder = path.join(cwd, "tmp");

function cleanSettings() {
    const settings = path.join(tmpFolder, ".vscode", "settings.json");

    if (existsSync(settings)) {
        writeFileSync(settings, "{}");
    }
}

/**
 * Some tests will need to wait for vscode to register the actions. An example will
 * be creating/killing terminals and configuration update.
 *
 * @param milliseconds - time to sleep
 * @returns
 */
export function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

export async function updateConfig(name: string, value: any) {
    vscode.extensions.getExtension("virgilsisoe.nuke-tools")?.activate();
    const nukeTools = vscode.workspace.getConfiguration("nukeTools");
    await nukeTools.update(name, value, vscode.ConfigurationTarget.Workspace);
}

suite("Socket", () => {
    const timeSleep = 500;

    suiteSetup("Setup Clean settings file", () => {
        cleanSettings();
    });

    teardown("Tear Down settings file", async () => {
        cleanSettings();
        // need to wait after the clean otherwise next test can pick up a file
        // before it was cleaned.
        await sleep(250);
    });

    test("Prepare debug message", () => {
        const debugMsg = socket.prepareDebugMsg();
        assert.ok(debugMsg.hasOwnProperty("text"));
        assert.ok(debugMsg.hasOwnProperty("file"));
    });

    test.skip("sendDebugMessage", () => {});

    test("Get NukeServerSocket.ini", () => {
        const iniPath = socket.getNukeIni();
        // TODO: this will fail if file was not created
        assert(require("fs").existsSync(iniPath));
    });

    test("Changing network addresses should not work if enableConnection is false", async () => {
        await updateConfig("network.host", "192.136.1.99");
        await updateConfig("network.port", "99999");

        const address = socket.getAddresses();
        assert.strictEqual(address, "host: 127.0.0.1 port: 54321");
    });

    test("Change network address when enableConnection is true", async () => {
        await updateConfig("network.enableManualConnection", true);
        await updateConfig("network.host", "192.186.1.00");
        await updateConfig("network.port", "55555");

        const address = socket.getAddresses();
        assert.strictEqual(address, "host: 192.186.1.00 port: 55555");
    });

    test("Get port value from fake.ini", () => {
        const fakeIni = path.join(tmpFolder, "fake.ini");
        writeFileSync(fakeIni, "[server]\nport=55555");

        const port = socket.getPortFromIni(fakeIni, "54321");
        assert.strictEqual(port, "55555");
    });

    test("Get default port value from fake.ini when value type is incorrect", () => {
        const fakeIni = path.join(tmpFolder, "fake.ini");
        const wrongValues = [
            "port",
            "port=",
            "port=true",
            "port=9999999",
            "port=value",
        ];

        for (const value of wrongValues) {
            writeFileSync(fakeIni, `[server]\n${value}`);
            const port = socket.getPortFromIni(fakeIni, "54321");
            assert.strictEqual(port, "54321");
        }
        writeFileSync(fakeIni, "");
    });
});

suite.skip("Send Data", () => {});
