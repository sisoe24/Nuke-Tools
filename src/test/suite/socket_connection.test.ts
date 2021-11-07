import * as assert from "assert";

import * as socket from "../../socket";
import * as testUtils from "./utils";

import { Server } from "net";

// ! TODO: not sure about all this

async function server(port = 54321, host = "localhost") {
    console.log("init server");

    const _server = new Server();
    _server.listen(port, host);

    await testUtils.sleep(100);

    _server.on("connection", function (socket) {
        socket.write("Hello,yo.");

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
    test("Send data to server", async () => {
        await server();
        const data = await socket.sendData("localhost", 54321, "hello");
        assert.strictEqual(data, "Message Received");
    });

    test("Send data but server is not connected", async () => {
        const data = await socket.sendData("localhost", 54321, "hello");
        assert.strictEqual(data, "Connection refused");
    });

    test("Send data but port is out of range", async () => {
        assert.throws(() => {
            socket.sendData("localhost", 124567, "hello");
        }, RangeError);
    });

    test.skip("Send data but host is unreachable", async () => {
        await socket.sendData("192.168.1.99", 12456, "hello");
    });
});
