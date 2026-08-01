import { defineConfig } from "vitest/config";

// Unit tests only. Scope to src/ so Vitest never tries to run the Playwright E2E
// specs under e2e/ (a different test runner). Playwright stays `npm run e2e`-style
// via playwright.config.ts; Vitest is `npm run test`.
export default defineConfig({
  test: {
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    exclude: ["node_modules", "dist", "e2e"],
    environment: "node",
  },
});
