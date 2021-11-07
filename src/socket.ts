import * as vscode from "vscode";
import * as utils from "./utils";
import * as os from "os";
import { Socket } from "net";
import * as fs from "fs";
import * as path from "path";

const outputWindow = vscode.window.createOutputChannel("Nuke Tools");

/**
 * Get the NukeServerSocket.ini file path.
 *
 * The path will be returned even if there is no file.
 *
 * @returns - path like string.
 */
export function getNukeIni(): string {
    return path.join(os.homedir(), ".nuke/NukeServerSocket.ini");
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
    const manualAddress = utils.nukeToolsConfig(`network.${property}`);

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
 * If NukeServerSocket.ini has a wrong value, will default back on `defaultPort`.
 *
 * @param configIni - path of the NukeServerSocket.ini.
 * @param defaultPort - default port value if ini file had no valid value.
 * @returns - the port value.
 */
export function getPortFromIni(configIni: string, defaultPort: string): string {
    const fileContent = fs.readFileSync(configIni, "utf-8");
    const match = fileContent.match(/port=(\d{5})(\b|\n)/);

    if (!match) {
        const msg = `
            The configuration for the server/port appears to be invalid.
            Falling back on port 54321 for now.
            Try disconnecting and connecting back the server inside Nuke.
            `;
        vscode.window.showErrorMessage(msg);
        return defaultPort;
    }

    return match[1];
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
export function getPort(): number {
    let port = "54321";

    const configIni = getNukeIni();
    if (fs.existsSync(configIni)) {
        port = getPortFromIni(configIni, port);
    }

    if (utils.nukeToolsConfig("network.enableManualConnection")) {
        port = getManualAddress("port", port);
    }
    return parseInt(port);
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

    if (utils.nukeToolsConfig("network.enableManualConnection")) {
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

/**
 * Write received data from the socket to the output window.
 *
 * @param data text data to write into the output window.
 * @param showDebug if true, the output window will not be cleared despite the settings.
 */
function writeToOutputWindow(data: string, showDebug: boolean): void {
    if (utils.nukeToolsConfig("other.clearPreviousOutput") && !showDebug) {
        outputWindow.clear();
    }

    const editor = vscode.window.activeTextEditor;
    if (editor) {
        outputWindow.appendLine(`> Executing: ${editor.document.fileName || "unknown"}`);
        outputWindow.appendLine(data);
        outputWindow.show(true);
    }
}

/**
 *  Write debug information to the output window.
 *
 * @param showDebug if true, will output debug information to the output window.
 * @param data text data to write into the output window.
 */
function writeDebugNetwork(showDebug: boolean, data: string): void {
    if (showDebug) {
        const timestamp = new Date();
        const msg = `[${timestamp.toISOString()}] - ${data}`;
        outputWindow.appendLine(msg);
    }
}

/**
 * Send data over TCP network.
 *
 * @param host - host address for the connection.
 * @param port - port address for the connection.
 * @param data - Stringified data to sent as code to be executed inside Nuke.
 * @param timeout - time for the timeout connection. Defaults to 10000 ms (10sec).
 */
export function sendData(host: string, port: number, data: string, timeout = 10000): void {
    const client = new Socket();
    const showDebug = utils.nukeToolsConfig("network.debug") as boolean;

    writeDebugNetwork(showDebug, `Try connecting to ${host}:${port}`);

    /**
     * Set connection timeout.
     *
     * Once emitted will close the socket with an error: 'connection timeout'.
     */
    client.setTimeout(timeout, () => {
        writeDebugNetwork(showDebug, "Connection timeout.");
        client.destroy(new Error("Connection timeout"));
    });

    try {
        /**
         * Initiate a connection on a given socket.
         *
         * If host is undefined, will fallback to localhost.
         */
        client.connect(port, host, function () {
            writeDebugNetwork(showDebug, "Connected.");
            client.write(data);
        });
    } catch (error) {
        if (error instanceof RangeError) {
            const msg = `Port is out of range. Value should be >= 49567 and < 65536. Received: ${port}`;
            writeDebugNetwork(showDebug, msg);
            client.destroy(new Error("Port out of range"));
        } else {
            writeDebugNetwork(showDebug, `Unknown exception. ${error.message}`);
            client.destroy(new Error(`${error}`));
        }
    }

    /**
     * Emitted when data is received.
     *
     * The argument data will be a Buffer or String. Encoding of data is set by socket.setEncoding().
     */
    client.on("data", function (data: string) {
        writeDebugNetwork(showDebug, `Received: "${data.toString().replace(/\n/g, "\\n")}"\n`);
        writeToOutputWindow(data, showDebug);
        client.destroy();
    });

    /**
     * Emitted after resolving the host name but before connecting.
     */
    client.on(
        "lookup",
        function (error: Error | null, address: string, family: string, host: string) {
            writeDebugNetwork(
                showDebug,
                "Socket Lookup :: " +
                    JSON.stringify(
                        { address: address, family: family, host: host, error: error },
                        null,
                        " "
                    )
            );

            // console.log(error);
            if (error) {
                writeDebugNetwork(showDebug, `${error.message}`);
            }
        }
    );

    /**
     * Emitted when an error occurs.
     *
     * The 'close' event will be called directly following this event.
     */
    client.on("error", function (error: Error) {
        const msg = `
            Couldn't connect to NukeServerSocket. Check the plugin and try again. 
            If manual connection is enable, verify that the port and host address are correct. 
            ${error.message}`;
        vscode.window.showErrorMessage(msg);
    });

    /**
     * Emitted when a socket is ready to be used.
     *
     * Triggered immediately after 'connect'.
     */
    client.on("ready", function () {
        writeDebugNetwork(showDebug, "Message ready.");
    });

    /**
     * Emitted once the socket is fully closed.
     */
    client.on("close", function (hadError: boolean) {
        writeDebugNetwork(showDebug, `Connection closed. Had Errors: ${hadError.toString()}`);
    });

    /**
     * Emitted when the other end of the socket signals the end of transmission.
     */
    client.on("end", function () {
        writeDebugNetwork(showDebug, "Connection ended.");
    });
}

/**
 * Prepare a debug message to send to the socket.
 *
 * Message contains some valid python code and will show the user information.
 *
 * @returns - data object
 */
export function prepareDebugMsg(): { text: string; file: string } {
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
export function sendDebugMessage(): void {
    sendData(getHost(), getPort(), JSON.stringify(prepareDebugMsg()));
}

/**
 * Prepare the message to be sent to the socket.
 *
 * If editor has no selected text, the whole file will be sent. Otherwise only
 * the selected text.
 *
 * @param editor - vscode TextEditor instance.
 * @returns a stringified object with the data to be sent.
 */
function prepareMessage(editor: vscode.TextEditor): string {
    const document = editor.document;
    const selection = editor.selection;
    const selectedWord = document.getText(selection);

    const data = {
        file: editor.document.fileName,
        text: selectedWord || editor.document.getText(),
    };
    return JSON.stringify(data);
}
/**
 * Send data over TCP connection.
 *
 * The data to be sent over will the current active file name and its content.
 * Data will be wrapped inside a stringified object before being sent.
 *
 *
 */
export function sendMessage(): void {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        return;
    }

    // the output window is treated as an active text editor, so if it has the
    // focus and user tries to execute the command, the text from the output window
    // window will be sent instead.
    if (editor.document.uri.scheme === "output") {
        vscode.window.showInformationMessage(
            "You currently have the Output window in focus. Return the focus on the text editor."
        );
        return;
    }

    sendData(getHost(), getPort(), prepareMessage(editor));
}
