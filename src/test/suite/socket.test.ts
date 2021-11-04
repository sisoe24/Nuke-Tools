import * as assert from "assert";
import * as path from "path";

import { writeFileSync } from "fs";

import * as socket from "../../socket";
import * as utils from "./utils";

suite("Socket", () => {
    suiteSetup("Setup Clean settings file", async () => {
        await utils.cleanSettings();
    });

    teardown("Tear Down settings file", async () => {
        await utils.cleanSettings();
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
        // TODO: should call Promise.all. but it doesn't work
        await utils.updateConfig("network.host", "192.136.1.99");
        await utils.updateConfig("network.port", "99999");

        const address = socket.getAddresses();
        assert.strictEqual(address, "host: 127.0.0.1 port: 54321");
    });

    test("Change network address when enableConnection is true", async () => {
        // TODO: should call Promise.all. but it doesn't work
        await utils.updateConfig("network.enableManualConnection", true);
        await utils.updateConfig("network.host", "192.186.1.00");
        await utils.updateConfig("network.port", "55555");

        const address = socket.getAddresses();
        assert.strictEqual(address, "host: 192.186.1.00 port: 55555");
    });

    test("Get port value from fake.ini", () => {
        const fakeIni = path.join(utils.tmpFolder(), "fake.ini");
        writeFileSync(fakeIni, "[server]\nport=55555");

        const port = socket.getPortFromIni(fakeIni, "54321");
        assert.strictEqual(port, "55555");
    });

    test("Get default port value from fake.ini when value type is incorrect", () => {
        const fakeIni = path.join(utils.tmpFolder(), "fake.ini");
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
