import { defineConfig, devices } from "@playwright/test";

/**
 * E2E config. Boots a FRESH backend in MOCK_LLM mode (deterministic, no Gemini
 * quota) on :8000 and the Vite dev server on :5173, then runs the specs.
 * Stop any manually-started servers first — reuseExistingServer is false so the
 * backend is always the mock one.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
    screenshot: "on",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: ".venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000 --log-level warning",
      cwd: "../backend",
      env: {
        MOCK_LLM: "1",
        MOCK_EMAIL: "1",
        MOCK_GOOGLE: "1",
        MOCK_WEB: "1",
        SYNC_ON_STARTUP: "0",
        CALENDAR_SYNC_ENABLED: "0",
        AUTO_EMAIL_ENABLED: "0",
        DEFAULT_RECIPIENT: "rep@salesintel.test",
        DATABASE_URL: "sqlite:///./e2e_salesintel.db",
        LLM_API_KEY: "test-key",
      },
      url: "http://localhost:8000/health",
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: "npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
