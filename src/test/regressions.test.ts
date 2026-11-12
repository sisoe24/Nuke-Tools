import * as assert from "assert";
import * as net from "net";
import * as vscode from "vscode";

import { sendData } from "../socket";
import { KnobFile } from "../nuke/nodes_tree";
import { nukeValidator } from "../nuke/nuke_script_diagnostic";
import { blinkScriptFormatter } from "../blinkscript/blink_format";

const validate = (text: string) =>
    nukeValidator({ getText: () => text } as vscode.TextDocument).map((d) => d.code);

suite("Regressions", () => {
    test("blinkscript formatter keeps a brace out of a line comment", () => {
        const formatted = blinkScriptFormatter("if (x) // check\n{\n  y = 1;\n}\n", 2);
        assert.ok(!formatted.includes("// check {"), formatted);
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
