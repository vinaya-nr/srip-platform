import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  esbuild: {
    jsx: "automatic",
    jsxImportSource: "react"
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup/vitest.setup.tsx"],
    include: ["tests/unit/**/*.test.ts", "tests/unit/**/*.test.tsx"],
    coverage: {
      provider: "istanbul",
      reporter: ["text", "html", "lcov"],
      reportsDirectory: "./coverage",
      include: [
        "components/**/*.tsx",
        "lib/**/*.ts",
        "stores/**/*.ts",
        "app/(public)/login/page.tsx",
        "app/(public)/register/page.tsx",
        "app/(protected)/settings/page.tsx"
      ],
      exclude: [
        "tests/**",
        "**/*.d.ts"
      ],
      thresholds: {
        lines: 75,
        branches: 70,
        statements: 80
      }
    }
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname)
    }
  }
});
