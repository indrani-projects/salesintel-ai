import { test, expect, request as pwRequest } from "@playwright/test";

const API = "http://localhost:8000";
const SHOTS = "e2e/screenshots";

async function seedMeeting(persona = "sales_rep") {
  const ctx = await pwRequest.newContext();
  const res = await ctx.post(`${API}/meetings`, {
    data: {
      subject: "Discovery call with The Sleep Company",
      prospect_company: "The Sleep Company",
      why: "Scale retail + B2B",
      agenda: "Omnichannel data + support",
      start_time: "2026-07-20T10:30:00",
      persona,
    },
  });
  expect(res.ok()).toBeTruthy();
  const m = await res.json();
  await ctx.dispose();
  return m.id as number;
}

// The app is gated by a client-side demo login. Seed the auth session so the shell
// renders for every test; the dedicated login test clears it to exercise the form.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "salesintel.auth",
      JSON.stringify({ name: "Rohan M.", persona: "sales_rep" }),
    );
  });
});

test("login page signs in with a persona and lands on the app", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.removeItem("salesintel.auth"));
  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await page.fill("#login-name", "Rohan M.");
  await page.fill("#login-password", "demo");
  await page.selectOption("#login-persona", "sales_rep");
  await page.screenshot({ path: `${SHOTS}/00-login.png`, fullPage: true });
  await page.getByRole("button", { name: /enter workspace/i }).click();
  await expect(page).toHaveURL(/\/calendar/);
  await expect(page.getByText("Rohan M.").first()).toBeVisible(); // sidebar reflects the user

  // Sign out returns to the login page.
  await page.getByRole("button", { name: /sign out/i }).click();
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("app shell renders with the workspace nav", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("SalesIntel AI").first()).toBeVisible();
  await expect(page.getByRole("button", { name: /new meeting/i }).first()).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/01-calendar.png`, fullPage: true });
});

test("create a meeting via the dialog lands on the dashboard", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /new meeting/i }).first().click();

  await expect(page.getByRole("dialog")).toBeVisible();
  // Company is now free-text — use an unknown, web-only company (no docs folder)
  // to prove web-first intel drives the brief.
  await page.fill("#m-subject", "Discovery call with Freshworks");
  await page.fill("#m-company", "Freshworks");
  await page.fill("#m-why", "Scale retail + B2B");
  await page.fill("#m-agenda", "Omnichannel data + support");
  await page.screenshot({ path: `${SHOTS}/02-dialog.png` });
  await page.getByRole("button", { name: "Create meeting" }).click();

  await expect(page.getByRole("dialog")).toBeHidden();
  await page.goto("/dashboard");
  await expect(page.getByText("Freshworks").first()).toBeVisible();
  await expect(page.getByText("Sales Representative").first()).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/03-dashboard.png`, fullPage: true });
});

test("brief view shows only the user's persona tab, and Scout answers", async ({ page }) => {
  const id = await seedMeeting("sales_rep");
  await page.goto(`/meeting/${id}`);

  // Sales Representative brief (the signed-in persona)
  await expect(page.getByRole("heading", { name: "The Sleep Company", level: 1 })).toBeVisible();
  await expect(page.getByText("Sales Representative · Brief")).toBeVisible();
  await expect(page.getByText("ARR")).toBeVisible();          // KPI strip
  await expect(page.getByText("₹700 Cr")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Pain Hypotheses/ })).toBeVisible(); // a Sales Rep section
  await expect(page.getByText(/Ready · \d+ source/)).toBeVisible();

  // Single-persona app: only the signed-in user's tab is shown — no switching.
  await expect(page.getByRole("tab", { name: "Sales Representative" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Sales Manager" })).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "VP of Sales" })).toHaveCount(0);
  await page.screenshot({ path: `${SHOTS}/04-brief-single-persona.png`, fullPage: true });

  // Scout answers ("Send" exact — distinct from the toolbar's "Send as email")
  await page.getByPlaceholder("Ask Scout…").fill("Who led their last round?");
  await page.getByRole("button", { name: "Send", exact: true }).click();
  await expect(page.getByText(/Mock grounded answer/)).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: `${SHOTS}/07-scout.png`, fullPage: true });
});

test("settings shows Google connected and syncs the calendar", async ({ page }) => {
  // Backend runs with MOCK_GOOGLE=1 → reports connected as mock@calendar.test.
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Settings", level: 1 })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Google \(Gmail \+ Calendar\)/ })).toBeVisible();
  await expect(page.getByText("Connected", { exact: true })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/mock@calendar\.test/)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/10-settings.png`, fullPage: true });

  // Sync the (mock) calendar → the Sleep Company event imports (or is already
  // present if the E2E DB was reused). Either way the sync reports a result.
  await page.getByRole("button", { name: /Sync calendar now/i }).click();
  await expect(page.getByText(/imported \d+ prospect meeting/i)).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: `${SHOTS}/11-settings-synced.png`, fullPage: true });
});

test("settings shows the automated-emails card", async ({ page }) => {
  // Backend runs with AUTO_EMAIL_ENABLED=0 → card renders "Off" with the config.
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Automated emails" })).toBeVisible();
  await expect(page.getByText(/Before the meeting:/)).toBeVisible();
  await expect(page.getByText(/60 min/)).toBeVisible();
  await expect(page.getByText(/rep@salesintel\.test/)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/12-settings-automation.png`, fullPage: true });
});

test("send-as-email composes a persona digest and demo-sends", async ({ page }) => {
  const id = await seedMeeting("sales_rep");
  await page.goto(`/meeting/${id}`);
  await expect(page.getByRole("heading", { name: "The Sleep Company", level: 1 })).toBeVisible();

  // Open the email dialog from the brief toolbar.
  await page.getByRole("button", { name: /send as email/i }).click();
  const dialog = page.getByRole("dialog", { name: /send brief as email/i });
  await expect(dialog).toBeVisible();

  // Recipient prefilled, subject + attachment composed, preview rendered.
  await expect(dialog.getByLabel("To")).not.toHaveValue("");
  await expect(dialog.getByText(/Sales Representative Brief/)).toBeVisible({ timeout: 20_000 });
  await expect(dialog.getByText(/-sales_rep-brief\.pdf/)).toBeVisible();
  await expect(dialog.getByText(/Demo mode/)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/08-email-dialog.png`, fullPage: true });

  // Confirm → demo-send success.
  await dialog.getByRole("button", { name: /confirm send/i }).click();
  await expect(page.getByText(/Demo send complete/)).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: `${SHOTS}/09-email-sent.png`, fullPage: true });
});
