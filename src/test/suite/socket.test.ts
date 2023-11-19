import * as assert from "assert";
import * as vscode from "vscode";
import * as path from "path";

import * as fs from "fs";

import * as socket from "../../socket";
import * as utils from "./test_utils";

const fakeIni = path.join(utils.demoPath, "fake.ini");
const tmpFile = path.join(utils.demoPath, "test.py");

suite("Socket", () => {
    suiteSetup("Setup Clean settings file", () => {
        utils.cleanSettings();
    });

    teardown("Tear Down settings file", () => {
        utils.cleanSettings();
    });

    test("Get manual address", async () => {
        // TODO: should call Promise.all. but it doesn't work
        await utils.updateConfig("network.enableManualConnection", true);
        await utils.updateConfig("network.host", "localhost");

        const address = socket.getManualAddress("host", "randomHost");
        assert.strictEqual(address, "localhost");
    });

    test("Get manual address but no address is saved", async () => {
        // TODO: should call Promise.all. but it doesn't work
        await utils.updateConfig("network.enableManualConnection", true);
        await utils.updateConfig("network.host", "");

        const address = socket.getManualAddress("host", "randomHost");
        assert.strictEqual(address, "randomHost");
    });

    test("Changing network addresses should not work if enableConnection is false", async () => {
        // TODO: should call Promise.all. but it doesn't work
        await utils.updateConfig("network.enableManualConnection", false);
        await utils.updateConfig("network.host", "192.136.1.99");
        await utils.updateConfig("network.port", "99999");

        const address = socket.getAddresses();
        assert.strictEqual(address, "host: 127.0.0.1 port: 54321");
    });

    test("Change network address when enableConnection is true", async () => {
        // TODO: should call Promise.all. but it doesn't work
        // XXX: check why NukeServerSocket workspace had this settings.
        await utils.updateConfig("network.enableManualConnection", true);
        await utils.updateConfig("network.host", "192.186.1.00");
        await utils.updateConfig("network.port", "55555");

        const address = socket.getAddresses();
        assert.strictEqual(address, "host: 192.186.1.00 port: 55555");
    });

    test("Get port value from fake.ini", () => {
        fs.writeFileSync(fakeIni, "[server]\nport=55555");

        const port = socket.getPortFromIni(fakeIni, "54321");
        assert.strictEqual(port, "55555");
    });

    test("Get default port value from fake.ini when value type is incorrect", () => {
        const wrongValues = ["port", "port=", "port=value", "port=1234", "port=123456"];

        for (const value of wrongValues) {
            fs.writeFileSync(fakeIni, `[server]\n${value}`);
            const port = socket.getPortFromIni(fakeIni, "54321");
            assert.strictEqual(port, "54321");
        }
        fs.writeFileSync(fakeIni, "");
    });

    test("Prepare debug message", () => {
        const debugMsg = socket.prepareDebugMsg();
        assert.ok(Object.prototype.hasOwnProperty.call(debugMsg, "text"));
        assert.ok(Object.prototype.hasOwnProperty.call(debugMsg, "file"));
    });

    test("Write debug network", () => {
        const msg = socket.logDebugNetwork("random msg");
        assert.match(msg, /\[[^\]]+] - random msg/);
    });

    test("Write to output window", () => {
        const msg = socket.writeToOutputWindow("random msg", tmpFile);
        assert.strictEqual(msg, `> Executing: ${tmpFile}\\nrandom msg`);
    });
});

suite("Prepare message", () => {
    setup("Focus file", async () => {
        await utils.focusDemoFile("test.py");
    });

    test("prepareMessage with no selection: entire document", () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const msg = socket.composeMessage(editor);

            assert.ok(Object.prototype.hasOwnProperty.call(msg, "text"));
            assert.ok(Object.prototype.hasOwnProperty.call(msg, "file"));

            assert.strictEqual(msg["file"], tmpFile);
            assert.strictEqual(msg["text"], "print('hello world')");
            assert.strictEqual(msg["text"], editor.document.getText());
        }
    });

    test("prepareMessage with selected text", () => {
        const editor = vscode.window.activeTextEditor;

        if (editor) {
            editor.selection = new vscode.Selection(
                new vscode.Position(0, 0),
                new vscode.Position(0, 5)
            );
            const msg = socket.composeMessage(editor);

            assert.ok(Object.prototype.hasOwnProperty.call(msg, "text"));
            assert.ok(Object.prototype.hasOwnProperty.call(msg, "file"));

            assert.strictEqual(msg["file"], tmpFile);
            assert.strictEqual(msg["text"], "print");
        }
    });
});
