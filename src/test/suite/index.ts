"use strict";

import * as path from "path";
import * as Mocha from "mocha";
import * as NYC from "nyc";
import * as glob from "glob";

// Simulates the recommended config option
// extends: "@istanbuljs/nyc-config-typescript",
import * as baseConfig from "@istanbuljs/nyc-config-typescript";

// Recommended modules, loading them here to speed up NYC init
// and minimize risk of race condition
import "ts-node/register";
import "source-map-support/register";

// Linux: prevent a weird NPE when mocha on Linux requires the window size from the TTY
// Since we are not running in a tty environment, we just implementt he method statically
const tty = require("tty");
if (!tty.getWindowSize) {
    tty.getWindowSize = (): number[] => {
        return [80, 75];
    };
}

export async function run(): Promise<void> {
    const testsRoot = path.resolve(__dirname, "..");

    // Setup coverage pre-test, including post-test hook to report
    const nyc = new NYC({
        ...baseConfig,
        cwd: path.join(__dirname, "..", "..", ".."),
        reporter: ["text-summary", "cobertura", "lcov"],
        all: true,
        silent: false,
        instrument: true,
        hookRequire: true,
        hookRunInContext: true,
        hookRunInThisContext: true,
        include: ["out/**/*.js"],
        exclude: ["out/test/**"],
    });
    await nyc.wrap();

    // Check the modules already loaded and warn in case of race condition
    // (ideally, at this point the require cache should only contain one file - this module)
    const myFilesRegex = /nuke-tools\/out/;
    const filterFn = myFilesRegex.test.bind(myFilesRegex);
    if (Object.keys(require.cache).filter(filterFn).length > 1) {
        console.warn(
            "NYC initialized after modules were loaded",
            Object.keys(require.cache).filter(filterFn)
        );
    }

    // Debug which files will be included/excluded
    // console.log('Glob verification', await nyc.exclude.glob(nyc.cwd));

    await nyc.createTempDirectory();
    // Create the mocha test
    const mocha = new Mocha({
        ui: "tdd",
        timeout: 10 * 1000,
    });

    // Color the stdout
    mocha.options.color = true;

    // Add all files to the test suite
    const files = glob.sync("**/*.test.js", { cwd: testsRoot });
    files.forEach((f) => mocha.addFile(path.resolve(testsRoot, f)));

    const failures: number = await new Promise((resolve) => mocha.run(resolve));
    await nyc.writeCoverageFile();

    // Capture text-summary reporter's output and log it in console
    console.log(await captureStdout(nyc.report.bind(nyc)));

    if (failures > 0) {
        throw new Error(`${failures} tests failed.`);
    }
}

async function captureStdout(fn: any) {
    let w = process.stdout.write,
        buffer = "";
    process.stdout.write = (s) => {
        buffer = buffer + s;
        return true;
    };
    await fn();
    process.stdout.write = w;
    return buffer;
}
