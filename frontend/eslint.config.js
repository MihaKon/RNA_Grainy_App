import js from "@eslint/js";
import { defineConfig, globalIgnores } from "eslint/config";
import prettier from "eslint-config-prettier/flat";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig([
  // Build output
  globalIgnores(["dist"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      // Core JavaScript mistakes
      js.configs.recommended,
      // Type-aware TypeScript checks: unsafe any, floating promises, etc.
      tseslint.configs.strictTypeChecked,
      // Consistent TypeScript style
      tseslint.configs.stylisticTypeChecked,
      // Rules of Hooks and complete effect dependencies
      reactHooks.configs.flat.recommended,
      // Component files export only components, so hot reload keeps state
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // Type-only imports use `import type`
      "@typescript-eslint/consistent-type-imports": "error",
    },
  },
  // Sorted imports: packages, then @/, then relative
  {
    plugins: { "simple-import-sort": simpleImportSort },
    rules: {
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
    },
  },
  // Config files run in Node
  {
    files: ["**/*.js"],
    extends: [js.configs.recommended],
    languageOptions: { globals: globals.node },
  },
  // Turns off rules that conflict with Prettier
  prettier,
]);
