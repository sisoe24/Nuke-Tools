import * as vscode from "vscode";
import * as utils from "./utils";
import * as os from "os";
import { Socket } from "net";
import { readFileSync } from "fs";

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
    const fileContent = readFileSync(configIni, "utf-8");
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
    if (require("fs").existsSync(configIni)) {
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

    sendData(prepareMessage(editor));
}

/**
 * Send data over TCP network.
 *
 * @param text - Stringified text to be sent as code to be executed inside Nuke.
 */
export function sendData(text: string) {
    // TODO: still need to test this.
    let client = new Socket();

    // server connects by default to localhost even when undefined is supplied.
    client.connect(getPort(), getHost(), function () {
        console.log("Socket -> Connected");
        client.write(text);
    });

    client.on(
        "lookup",
        function (error: Error | null, address: string, family: string, host: string) {
            console.log("Socket -> error ::", error);
            console.log("Socket -> address ::", address);
            console.log("Socket -> family ::", family);
            console.log("Socket -> host ::", host);
        }
    );

    client.on("error", function (error: Error) {
        const msg = `
        Couldn't connect to NukeServerSocket. Check the plugin and try again.
        If manual connection is enable, verify that the port and host address are correct.
        [Error: ${error.message}]`;

        vscode.window.showErrorMessage(msg);
    });

    client.on("data", function (data: Buffer | string) {
        // Encoding of data is set by socket.setEncoding().

        console.log(`Socket -> Received :: ${data} of type ${typeof data}`);
        client.destroy(); // kill client after server's response

        const clearOutput = utils.nukeToolsConfig("other.clearPreviousOutput");
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
