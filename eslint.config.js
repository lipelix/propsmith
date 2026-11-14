import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import prettier from "eslint-config-prettier";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig(
  { ignores: ["dist", ".cache", "site/dist", "site/public/data"] },
  js.configs.recommended,
  tseslint.configs.strict,
  prettier,
  { languageOptions: { globals: { ...globals.node } } },
  {
    files: ["site/src/**"],
    languageOptions: { globals: { ...globals.browser } },
  },
);
