let net = require('net');
import { error } from 'console';
import * as vscode from 'vscode';
import * as utils from "./utils";

const os = require('os');
const output = vscode.window.createOutputChannel('Nuke Tools');

// Send test message to Server
export function sendTestMessage() {
    const random = () => Math.round(Math.random() * 10);
    const r1 = random();
    const r2 = random();
    const sum = r1 * r2;

    const hostname = os.hostname();
    const username = os.userInfo()['username'];

    const data = {
        'file': 'vscode/path/tmp_file.py',
        'text': `from __future__ import print_function;result = ${sum};print("Hello from host: ${hostname} user: ${username} (vscode test client). ${r1} * ${r2} =", result)`
    };

    // sendText(`print("Hello From Vscode Test function: ${sum}")`);
    sendText(JSON.stringify(data));
}

// Get Nuke ini in home directory
function getNukeIni() {

    const nukeConfigPath = require('path').join(
        os.homedir(), '.nuke/NukeServerSocket.ini'
    );

    return nukeConfigPath;
}

// Establish the connection source. check if manual config is enabled then 
// check for manual config. if none then fallback on default.
function checkManualConnection(field: string, config: string): string {

    if (utils.getConfiguration('network.enableManualConnection')) {
        const extField = utils.getConfiguration(`network.${config}`);

        if (!extField) {
            const manualErrorMsg = "You have enabled Manual Connection but Network: # appears to be empty. Falling back on default.";

            vscode.window.showErrorMessage(
                manualErrorMsg.replace('#', config)
            );
            return field;
        }
        return extField;
    }
    return field;

}

function getPort(): string {


    let port = '54321';
    const configIni = getNukeIni();

    if (require('fs').existsSync(configIni)) {
        const loadIniFile = require('read-ini-file');
        const iniContent = loadIniFile.sync(configIni);

        let errMsg;
        try {
            port = iniContent['server']['port'];
        } catch (err: unknown) {
            // server/port doesn't exists?
            errMsg = err;
        } finally {
            // port could be empty or be a boolean if it has no value assigned
            if (!port || errMsg ||typeof port === 'boolean') {
                port = '54321';
                const msg = `
                The configuration for the server/port appears to be invalid.
                Falling back on port 54321 for now.
                Try disconnecting and connecting back the server inside Nuke.
                Error: ${errMsg}
                `
                vscode.window.showErrorMessage(msg);
            }
        }
    }

    port = checkManualConnection(port, 'port');

    console.log(`port: ${port}`);
    return port;

}

function getHost() {
    let host = '127.0.0.1';

    host = checkManualConnection(host, 'host');

    console.log(`host: ${host}`);
    return host;
}

// Display addresses to user 
export function getAddresses() {
    return `host: ${getHost()} port: ${getPort()}`;
}

async function connectionError(err: Error) {
    const msg = "Couldn't connect to Nuke Server.\nCheck the Nuke plugin and try again. If manual connection is enable, verify that the port and host address are correct.";

    const showMessage = await vscode.window.showErrorMessage(msg, 'Show Error');

    if (showMessage) {
        vscode.window.showErrorMessage(err.message);
    }
}

export function sendText(text: string) {
    let client = new net.Socket();

    // XXX: server appears to connected by default to localhost even when undefined is supplied.
    client.connect(getPort(), getHost(), function () {
        console.log('socketClient -> Connected');
        client.write(text);
    });

    client.on('lookup', function (error: Error | null, address: string, family: string, host: string) {

        console.log('socketClient -> error ::', error);
        console.log('socketClient -> address ::', address);
        console.log('socketClient -> family ::', family);
        console.log('socketClient -> host ::', host);
    });


    client.on('error', function (error: Error) {
        connectionError(error);
    });

    client.on('data', function (data: Buffer | string) {
        // Encoding of data is set by socket.setEncoding().

        console.log(`socketClient -> Received :: ${data} of type ${typeof data}`);
        client.destroy(); // kill client after server's response

        const clearOutput = utils.getConfiguration('other.clearPreviousOutput');
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

    client.on('close', function (hadError: boolean) {
        console.log('SocketClient -> Connection closed -> Had Errors? ::', hadError);
    });

    client.on('end', function () {
        console.log('SocketClient -> Connection ended');
    });

}
