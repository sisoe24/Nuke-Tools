import js from "@eslint/js";
import tseslint from "typescript-eslint";
import { defineConfig } from "eslint/config";

export default defineConfig(
    {
        ignores: ["out", "dist", "demo", "**/*.d.ts"],
    },
    js.configs.recommended,
    tseslint.configs.recommended,
    {
        files: ["**/*.ts"],
        rules: {
            "@typescript-eslint/naming-convention": "warn",
            // `import x = require()` is the TypeScript form for `export =` modules like extract-zip
            "@typescript-eslint/no-require-imports": ["error", { allowAsImport: true }],
            "no-undef": "off",
            curly: "warn",
            eqeqeq: "warn",
            "no-throw-literal": "warn",
            semi: "warn",
        },
    }
);
