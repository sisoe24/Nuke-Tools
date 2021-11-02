import * as vscode from "vscode";
import * as utils from "./utils";
import * as os from "os";

let net = require("net");

const output = vscode.window.createOutputChannel("Nuke Tools");

/**
 * Prepare a debug message to send to the socket.
 *
 * Message contains some valid python code and will show the user information.
 *
 * @returns - data object
 */
export function prepareDebugMsg(): object {
    const random = () => Math.round(Math.random() * 10);
    const r1 = random();
    const r2 = random();

    let code = `
    from __future__ import print_function
    print("Hostname: ${os.hostname()} User: ${os.userInfo()["username"]}")
    print("Connected to ${getAddresses()}")
    print("${r1} * ${r2} =", ${r1 * r2})
    `;

    // make everything a single line python command
    code = code.trim().replace(/\n/g, ";");

    const data = {
        text: code,
        file: "vscode/path/tmp_file.py",
    };

    return data;
}

/**
 * Send a debug test message to the socket connection.
 */
export function sendDebugMessage() {
    sendText(JSON.stringify(prepareDebugMsg()));
}

/**
 * Get the NukeServerSocket.ini file path.
 *
 * The path will be returned even if there is no file.
 *
 * @returns - path like string.
 */
export function getNukeIni(): string {
    return require("path").join(os.homedir(), ".nuke/NukeServerSocket.ini");
}

/**
 * Get the manual address by looking in the configuration network property.
 *
 * Enable manual address could be enabled, but property could be empty, in that
 * case will show an error message to user and return the `defaultValue`.
 *
 * @param property - property name (port, host) to get from the configuration.
 * @param defaultValue - a default value to fallback in case property is undefined.
 * @returns - the property value.
 */
function getManualAddress(property: string, defaultValue: string): string {
    const manualAddress = utils.getConfig(`network.${property}`);

    if (!manualAddress) {
        const manualErrorMsg = `
        You have enabled Manual Connection but "Network: #"
        configuration appears to be empty. Falling back on default.
        `;
        vscode.window.showErrorMessage(manualErrorMsg.replace("#", property));
        return defaultValue;
    }
    return manualAddress;
}

/**
 * Get the port value from the NukeServerSocket.ini.
 *
 * If NukeServerSocket.ini has a wrong value (no value, boolean value or incorrect port),
 * will default back on `defaultPort`.
 *
 * @param configIni - path of the NukeServerSocket.ini.
 * @param defaultPort - default port value if ini file had no valid value.
 * @returns - the port value.
 */
function getPortFromIni(configIni: string, defaultPort: string): string {
    const loadIniFile = require("read-ini-file");
    const iniContent = loadIniFile.sync(configIni);

    let port = iniContent["server"]["port"];

    if (!port || typeof port !== "string" || !port.match(/\d{5}/)) {
        const msg = `
            The configuration for the server/port appears to be invalid.
            Falling back on port 54321 for now.
            Try disconnecting and connecting back the server inside Nuke.
            `;
        vscode.window.showErrorMessage(msg);
        return defaultPort;
    }

    return port;
}

/**
 * Get the port configuration value.
 *
 * The order of which the port value is taken is as follows:
 *  1. Create a default port value of: 54321
 *  2. If NukeServerSocket.ini has a valid port value, will be taken instead.
 *  3. If manual configuration is enabled, will be taken instead.
 *
 * If step 2 or 3 will fail, will default back on step 1.
 *
 * @returns - port value for the connection.
 */
export function getPort(): string {
    let port = "54321";

    const configIni = getNukeIni();
    if (require("fs").existsSync(configIni)) {
        port = getPortFromIni(configIni, port);
    }

    if (utils.getConfig("network.enableManualConnection")) {
        port = getManualAddress("port", port);
    }
    return port;
}

/**
 * Get the host address.
 *
 * Default host address will be local: 127.0.0.1. If manual connection is enabled
 * value will be updated from the configuration value.
 *
 * @returns - host address
 */
function getHost(): string {
    let host = "127.0.0.1";

    if (utils.getConfig("network.enableManualConnection")) {
        host = getManualAddress("host", host);
    }

    return host;
}

/**
 * Get the network addresses.
 *
 * This will create a simple string: `host: "hostname" port: "port"`
 *
 * @returns - string with the network addresses information.
 */
export function getAddresses(): string {
    return `host: ${getHost()} port: ${getPort()}`;
}

async function connectionError(err: Error) {
    const msg = `
    Couldn't connect to NukeServerSocket. Check the plugin and try again.
    If manual connection is enable, verify that the port and host address are correct.
    `;

    const showMessage = await vscode.window.showErrorMessage(msg, "Show Error");

    if (showMessage) {
        vscode.window.showErrorMessage(err.message);
    }
}

/**
 * Send data over TCP network.
 *
 * @param text - Stringified text to be sent as code to be executed inside Nuke.
 */
export function sendText(text: string) {
    let client = new net.Socket();

    // server connects by default to localhost even when undefined is supplied.
    client.connect(getPort(), getHost(), function () {
        console.log("Socket -> Connected");
        client.write(text);
    });

    client.on(
        "lookup",
        function (
            error: Error | null,
            address: string,
            family: string,
            host: string
        ) {
            console.log("Socket -> error ::", error);
            console.log("Socket -> address ::", address);
            console.log("Socket -> family ::", family);
            console.log("Socket -> host ::", host);
        }
    );

    client.on("error", function (error: Error) {
        connectionError(error);
    });

    client.on("data", function (data: Buffer | string) {
        // Encoding of data is set by socket.setEncoding().

        console.log(`Socket -> Received :: ${data} of type ${typeof data}`);
        client.destroy(); // kill client after server's response

        const clearOutput = utils.getConfig("other.clearPreviousOutput");
        if (clearOutput) {
            output.clear();
        }

        const editor = vscode.window.activeTextEditor;
        if (editor) {
            output.appendLine(`> Executing: ${editor.document.fileName} `);
        }
        output.appendLine(data as string);
        output.show(true);
    });

    client.on("close", function (hadError: boolean) {
        console.log("Socket -> Connection closed. Had Errors? ::", hadError);
    });

    client.on("end", function () {
        console.log("Socket -> Connection ended");
    });
}
