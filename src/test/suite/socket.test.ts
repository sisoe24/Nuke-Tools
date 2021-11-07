import * as assert from "assert";
import * as path from "path";

import * as fs from "fs";

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
        assert.ok(Object.prototype.hasOwnProperty.call(debugMsg, "text"));
        assert.ok(Object.prototype.hasOwnProperty.call(debugMsg, "file"));
    });

    test.skip("sendDebugMessage", () => {});

    test("Get NukeServerSocket.ini", () => {
        const iniPath = socket.getNukeIni();
        // ! TODO: this will fail if file was not created
        assert(fs.existsSync(iniPath));
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
        // ! TODO: check why NukeServerSocket workspace had this settings.
        await utils.updateConfig("network.enableManualConnection", true);
        await utils.updateConfig("network.host", "192.186.1.00");
        await utils.updateConfig("network.port", "55555");

        const address = socket.getAddresses();
        assert.strictEqual(address, "host: 192.186.1.00 port: 55555");
    });

    test("Get port value from fake.ini", () => {
        const fakeIni = path.join(utils.getTmpFolder(), "fake.ini");
        fs.writeFileSync(fakeIni, "[server]\nport=55555");

        const port = socket.getPortFromIni(fakeIni, "54321");
        assert.strictEqual(port, "55555");
    });

    test("Get default port value from fake.ini when value type is incorrect", () => {
        const fakeIni = path.join(utils.getTmpFolder(), "fake.ini");
        const wrongValues = ["port", "port=", "port=value", "port=1234", "port=123456"];

        for (const value of wrongValues) {
            fs.writeFileSync(fakeIni, `[server]\n${value}`);
            const port = socket.getPortFromIni(fakeIni, "54321");
            assert.strictEqual(port, "54321");
        }
        fs.writeFileSync(fakeIni, "");
    });
});
