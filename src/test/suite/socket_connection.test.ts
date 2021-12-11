import * as assert from "assert";

import * as socket from "../../socket";
import * as testUtils from "./test_utils";

import { Server } from "net";

// ! TODO: not sure about all this

async function server(port = 54321, host = "localhost") {
    console.log("init server");

    const _server = new Server();
    _server.listen(port, host);

    await testUtils.sleep(100);

    _server.on("connection", function (socket) {
        socket.write("Hello, server.");

        socket.on("data", function (chunk) {
            console.log(`Server :: Data received from client: ${chunk.toString()}`);
        });

        socket.on("end", function () {
            console.log("Server :: Closing connection with the client");
            _server.close();
        });
    });

    _server.on("close", () => {
        console.log("Server :: Closing server.");
    });
}

suite("Send Data", () => {
    const data = JSON.stringify({ text: "hello", file: "random.file" });

    test("Send data to server", async () => {
        await server();
        const received = await socket.sendData("localhost", 54321, data);
        assert.strictEqual(received.error, false);
        assert.strictEqual(received.message, "Hello, server.");
    });

    test("Send data but server is not connected", async () => {
        const received = await socket.sendData("localhost", 54321, data);
        assert.strictEqual(received.message, "Connection refused");
        assert.strictEqual(received.error, true);
    });

    test("Send data but port is out of range", async () => {
        const received = await socket.sendData("localhost", 654321, data);
        assert.strictEqual(received.message, "Connection refused");
        assert.strictEqual(received.error, true);
        assert.strictEqual(received.errorMessage, "Port is out of range");
    });

    test("Send data but host is unreachable", async () => {
        const received = await socket.sendData("1982.168.1.99", 12456, "hello");

        assert.strictEqual(received.error, true);
        assert.match(received.errorMessage, /getaddrinfo ENOTFOUND/);
        assert.strictEqual(received.message, "Connection refused");
    });

    test("sendDebugMessage", async () => {
        // TODO: how to be sure that connection is closed
        const received = await socket.sendDebugMessage();
        assert.strictEqual(received.error, true);
        assert.strictEqual(received.message, "Connection refused");
    });

    test("sendMessage connected", async () => {
        await server();

        const received = await socket.sendMessage();
        if (received) {
            assert.strictEqual(received.error, false);
            assert.strictEqual(received.message, "Hello, server.");
        }
    });

    test("sendMessage no connection", async () => {
        // TODO: how to be sure that connection is closed

        const received = await socket.sendMessage();
        if (received) {
            assert.strictEqual(received.error, true);
            assert.strictEqual(received.message, "Connection refused");
        }
    });

    test.skip("sendMessage but no active editor");
    test.skip("sendMessage but active editor is output window");
});
