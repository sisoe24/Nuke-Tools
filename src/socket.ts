import * as os from "os";
import * as nuke from "./nuke";
import * as vscode from "vscode";
import { getConfig } from "./config";

import { Socket } from "net";

const outputWindow = vscode.window.createOutputChannel("Nuke Tools");


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
    const manualAddress = getConfig(`network.${property}`) as string;

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


export function getPort(): number {

    let port = nuke.getNssConfig('port', '54321');

    if (getConfig("network.enableManualConnection")) {
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

    if (getConfig("network.enableManualConnection")) {
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
export function writeToOutputWindow(data: string, filePath: string): string {
    if (getConfig("other.clearPreviousOutput") && !getConfig("network.debug")) {
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
export function logDebugNetwork(data: string): string {
    if (!getConfig("network.debug")) {
        return "";
    }

    const timestamp = new Date();
    const msg = `[${timestamp.toISOString()}] - ${data}`;
    outputWindow.appendLine(msg);
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
    return new Promise((resolve, reject) => {
        const client = new Socket();
        const status = {
            message: "",
            error: false,
            errorMessage: "",
        };

        logDebugNetwork(`Try connecting to ${host}:${port}`);

        /**
         * Set connection timeout.
         *
         * Once emitted will close the socket with an error: 'connection timeout'.
         */
        client.setTimeout(timeout, () => {
            logDebugNetwork("Connection timeout.");
            client.destroy(new Error("Connection timeout"));
            reject(status);
        });

        try {
            /**
             * Initiate a connection on a given socket.
             *
             * If host is undefined, will fallback to localhost.
             */
            client.connect(port, host, function () {
                logDebugNetwork("Connected.");
                client.write(text);
            });
        } catch (error) {
            if (error instanceof RangeError) {
                const msg = `Port is out of range. Value should be >= 49567 and < 65536. Received: ${port}`;
                logDebugNetwork(msg);
                client.destroy(new Error("Port out of range"));
                status.errorMessage = "Port is out of range";
            } else {
                const msg = `Unknown exception. ${String(error)}`;
                logDebugNetwork(msg);
                client.destroy(new Error(msg));
                status.errorMessage = msg;
            }
            status.error = true;
            reject(status);
        }

        /**
         * Emitted when data is received.
         *
         * The argument data will be a Buffer or String. Encoding of data is set by socket.setEncoding().
         */
        client.on("data", function (data: string | Buffer) {
            const textData = data.toString();

            const oneLineData = textData.replace(/\n/g, "\\n");
            logDebugNetwork(`Received: "${oneLineData}"\n`);

            const filePath = JSON.parse(text)["file"];
            writeToOutputWindow(textData, filePath);

            status.message = data.toString().trim();
            resolve(status);
            client.end();
        });

        /**
         * Emitted after resolving the host name but before connecting.
         */
        client.on(
            "lookup",
            function (error: Error | null, address: string, family: string, host: string) {
                logDebugNetwork(
                    "Socket Lookup :: " +
                        JSON.stringify({ address, family, host, error }, null, " ")
                );

                if (error) {
                    logDebugNetwork(`${error.message}`);
                    status.errorMessage = error.message;
                    reject(status);
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

            status.errorMessage = "Connection refused";
            status.error = true;
            reject(status);
        });

        /**
         * Emitted when a socket is ready to be used.
         *
         * Triggered immediately after 'connect'.
         */
        client.on("ready", function () {
            logDebugNetwork("Message ready.");
        });

        /**
         * Emitted once the socket is fully closed.
         */
        client.on("close", function (hadError: boolean) {
            logDebugNetwork(`Connection closed. Had Errors: ${hadError.toString()}`);
        });

        /**
         * Emitted when the other end of the socket signals the end of transmission.
         */
        client.on("end", function () {
            logDebugNetwork("Connection ended.");
        });
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

    const code = `
    from __future__ import print_function
    print("Hostname: ${os.hostname() as string} User: ${os.userInfo()["username"] as string}")
    print("Connected to ${getAddresses()}")
    print("${r1} * ${r2} =", ${r1 * r2})
    `;

    return {
        text: code.trim().replace(/\n/g, ";"),
        file: "tmp_file",
    };
}

/**
 * Send a debug test message to the socket connection.
 */
export async function sendDebugMessage(): Promise<{
    message: string;
    error: boolean;
    errorMessage: string;
}> {
    return await sendData(getHost(), getPort(), JSON.stringify(prepareDebugMsg()));
}

/**
 * Send the current active file to the socket.
 *
 * The data to be sent over will the current active file name and its content.
 * Data will be wrapped inside a stringified object before being sent.
 *
 */
export async function sendMessage(): Promise<
    | Promise<{
          message: string;
          error: boolean;
          errorMessage: string;
      }>
    | undefined
> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        return;
    }

    // for some reason, the output window is considered as an active editor.
    if (editor.document.uri.scheme === "output") {
        vscode.window.showInformationMessage(
            "You currently have the Output window in focus. Return the focus on the text editor."
        );
        return;
    }

    const data = {
        file: editor.document.fileName,
        text: editor.document.getText(editor.selection) || editor.document.getText(),
    };

    return await sendData(getHost(), getPort(), JSON.stringify(data));
}

/**
 * Send an arbitrary command to the socket.
 *
 * @param command a stringified command to be sent to the socket.
 * @returns
 */
export function sendCommand(command: string): Promise<{
    message: string;
    error: boolean;
    errorMessage: string;
}> {
    return sendData(getHost(), getPort(), command);
}
