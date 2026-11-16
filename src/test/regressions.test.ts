import * as assert from "assert";
import * as net from "net";
import * as path from "path";
import * as vscode from "vscode";

import { sendData } from "../socket";
import { isNewerVersion } from "../packages";
import { replaceStubsPath, stubsAssets } from "../stubs";
import { KnobFile } from "../nuke/nodes_tree";
import { nukeValidator } from "../nuke/nuke_script_diagnostic";
import { blinkScriptFormatter } from "../blinkscript/blink_format";
import { nukeScriptFormatter } from "../nuke/nuke_script_format";

const validate = (text: string) =>
    nukeValidator({ getText: () => text } as vscode.TextDocument).map((d) => d.code);

suite("Regressions", () => {
    test("stubs assets are read from the versioned zip names", () => {
        const asset = (name: string) => ({ name, browser_download_url: `https://x/${name}` });
        const release = {
            tag_name: "v0.4.0",
            html_url: "",
            assets: [
                asset("nuke-python-stubs-15.2v9.zip"),
                asset("nuke-python-stubs-15.2v10.zip"),
                asset("nuke-python-stubs-17.1v2.zip"),
                asset("nuke-python-stubs.zip"),
                asset("nuke-python-stubs-...zip"),
                asset("nuke-python-stubs-15.2v9.tar.gz"),
            ],
        };
        assert.deepStrictEqual(stubsAssets(release), [
            { version: "17.1v2", url: "https://x/nuke-python-stubs-17.1v2.zip" },
            { version: "15.2v10", url: "https://x/nuke-python-stubs-15.2v10.zip" },
            { version: "15.2v9", url: "https://x/nuke-python-stubs-15.2v9.zip" },
        ]);
    });

    test("only one stubs version stays in extraPaths", () => {
        const root = path.join(path.sep, "home", ".nuke", "NukeTools", "stubs");
        const other = path.join(path.sep, "libs");
        const paths = [path.join(root, "15.2v9"), other, root, path.join(root, "17.1v2")];
        assert.deepStrictEqual(replaceStubsPath(paths, root, path.join(root, "17.1v2")), [
            other,
            path.join(root, "17.1v2"),
        ]);
        assert.deepStrictEqual(replaceStubsPath([`${root}-old`], root, root + "/x"), [
            `${root}-old`,
            root + "/x",
        ]);
    });

    test("version compare is numeric, not lexical", () => {
        assert.ok(isNewerVersion("0.18.0", "0.9.0"));
        assert.ok(isNewerVersion("v1.10.0", "1.4.2"));
        assert.ok(isNewerVersion("1.4.2.1", "1.4.2"));
        assert.ok(!isNewerVersion("1.4.2", "v1.4.2"));
        assert.ok(!isNewerVersion("1.4.2", "1.5.0"));
    });

    test("blinkscript formatter keeps a brace out of a line comment", () => {
        const formatted = blinkScriptFormatter("if (x) // check\n{\n  y = 1;\n}\n", 2);
        assert.ok(!formatted.includes("// check {"), formatted);
    });

    test("nuke formatter gives the same result when run twice", () => {
        const script = "Grade {\n curves {\n  a b\n }\n name G\n}\nGrade {\n curves {x}\n name G2\n}\n";
        const once = nukeScriptFormatter(script, 2);
        assert.strictEqual(nukeScriptFormatter(once, 2), once);
        assert.ok(once.includes("\n}\nGrade {\n  curves {x}\n  name G2\n}"), once);
    });

    test("nuke validator accepts valid scripts", () => {
        assert.deepStrictEqual(validate('Grade {\n disable {{"\\$gui"}}\n}\n'), []);
        assert.deepStrictEqual(validate("set N1 [stack 12]\npush $N1\n"), []);
        assert.deepStrictEqual(validate('Text2 {\n message "{"\n}\n'), []);
    });

    test("nuke validator reports an undefined stack variable", () => {
        assert.deepStrictEqual(validate("push $N1\n"), ["undefined-variable"]);
    });

    test("knob file names with underscores parse", () => {
        const knobFile = new KnobFile("my_node--Grade--my_knob--123.py");
        assert.deepStrictEqual(
            [knobFile.node, knobFile.nodeClass, knobFile.knob, knobFile.id],
            ["my_node", "Grade", "my_knob", "123"]
        );
    });

    test("legacy knob file names still parse", () => {
        const knobFile = new KnobFile("Grade1_Grade_mix_123.py");
        assert.deepStrictEqual(
            [knobFile.node, knobFile.nodeClass, knobFile.knob, knobFile.id],
            ["Grade1", "Grade", "mix", "123"]
        );
    });

    test("socket reply spanning several chunks is returned whole", async () => {
        const server = net.createServer((socket) => {
            socket.once("data", () => {
                socket.write("first ");
                setTimeout(() => socket.end("second"), 50);
            });
        });
        await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));

        try {
            const port = (server.address() as net.AddressInfo).port;
            const result = await sendData("127.0.0.1", port, JSON.stringify({ file: "", text: "" }));
            assert.strictEqual(result.message, "first second");
        } finally {
            server.close();
        }
    });
});
