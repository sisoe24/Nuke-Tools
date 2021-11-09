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
export function getManualAddress(property: string, defaultValue: string): string {
    const manualAddress = utils.nukeToolsConfig(`network.${property}`) as string;

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
 * @param filePath path to the file that is being executed.
 * @param showDebug if true, the output window will not be cleared despite the settings.
 */
export function writeToOutputWindow(data: string, filePath: string, showDebug: boolean): string {
    if (utils.nukeToolsConfig("other.clearPreviousOutput") && !showDebug) {
        outputWindow.clear();
    }

    const msg = `> Executing: ${filePath}\n${data}`;

    outputWindow.appendLine(msg);
    outputWindow.show(true);

    return msg.replace(/\n/g, "\\n");
}

/**
 *  Write debug information to the output window.
 *
 * @param showDebug if true, will output debug information to the output window.
 * @param data text data to write into the output window.
 */
export function writeDebugNetwork(showDebug: boolean, data: string): string {
    let msg = "";

    if (showDebug) {
        const timestamp = new Date();
        msg = `[${timestamp.toISOString()}] - ${data}`;
        outputWindow.appendLine(msg);
    }
    return msg;
}

/**
 * Send data over TCP network.
 *
 * @param host - host address for the connection.
 * @param port - port address for the connection.
 * @param text - Stringified text to sent as code to be executed inside Nuke.
 * @param timeout - time for the timeout connection. Defaults to 10000 ms (10sec).
 */
export async function sendData(
    host: string,
    port: number,
    text: string,
    timeout = 10000
): Promise<{ message: string; error: boolean; errorMessage: string }> {
    // TODO: should make a class.

    const client = new Socket();
    const showDebug = utils.nukeToolsConfig("network.debug") as boolean;
    const status = {
        message: "",
        error: false,
        errorMessage: "",
    };

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
            client.write(text);

            status.message = "Connected";
        });
    } catch (error) {
        if (error instanceof RangeError) {
            const msg = `Port is out of range. Value should be >= 49567 and < 65536. Received: ${port}`;
            writeDebugNetwork(showDebug, msg);
            client.destroy(new Error("Port out of range"));

            status.errorMessage = "Port is out of range";
        } else {
            const msg = `Unknown exception. ${String(error)}`;
            writeDebugNetwork(showDebug, msg);
            client.destroy(new Error(msg));

            status.errorMessage = msg;
        }
    }

    /**
     * Emitted when data is received.
     *
     * The argument data will be a Buffer or String. Encoding of data is set by socket.setEncoding().
     */
    client.on("data", function (data: string | Buffer) {
        const textData = data.toString();

        const oneLineData = textData.replace(/\n/g, "\\n");
        writeDebugNetwork(showDebug, `Received: "${oneLineData}"\n`);

        const filePath = JSON.parse(text)["file"];
        writeToOutputWindow(textData, filePath, showDebug);

        client.end();
        status.message = data.toString();
    });

    /**
     * Emitted after resolving the host name but before connecting.
     */
    client.on(
        "lookup",
        function (error: Error | null, address: string, family: string, host: string) {
            writeDebugNetwork(
                showDebug,
                "Socket Lookup :: " + JSON.stringify({ address, family, host, error }, null, " ")
            );

            if (error) {
                writeDebugNetwork(showDebug, `${error.message}`);
                status.errorMessage = error.message;
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

        status.message = "Connection refused";
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
        status.error = hadError;
    });

    /**
     * Emitted when the other end of the socket signals the end of transmission.
     */
    client.on("end", function () {
        writeDebugNetwork(showDebug, "Connection ended.");
    });

    // ! TODO: not confident about this
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(status);
        }, 100);
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
    print("Hostname: ${os.hostname() as string} User: ${os.userInfo()["username"] as string}")
    print("Connected to ${getAddresses()}")
    print("${r1} * ${r2} =", ${r1 * r2})
    `;

    // make everything a single line python command
    code = code.trim().replace(/\n/g, ";");

    const data = {
        text: code,
        file: "tmp_file",
    };

    return data;
}

/**
 * Send a debug test message to the socket connection.
 */
export function sendDebugMessage() {
    return sendData(getHost(), getPort(), JSON.stringify(prepareDebugMsg()));
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
export function prepareMessage(editor: vscode.TextEditor): { text: string; file: string } {
    const document = editor.document;
    const selection = editor.selection;
    const selectedText = document.getText(selection);

    const data = {
        file: editor.document.fileName,
        text: selectedText || editor.document.getText(),
    };
    return data;
}

/**
 * Send data over TCP connection.
 *
 * The data to be sent over will the current active file name and its content.
 * Data will be wrapped inside a stringified object before being sent.
 *
 */
export function sendMessage() {
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

    return sendData(getHost(), getPort(), JSON.stringify(prepareMessage(editor)));
}
