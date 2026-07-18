import { test, expect, request as pwRequest } from "@playwright/test";

const API = "http://localhost:8000";
const SHOTS = "e2e/screenshots";

async function seedMeeting(persona = "ae") {
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
  await page.fill("#m-subject", "Discovery call with The Sleep Company");
  await page.selectOption("#m-company", "The Sleep Company");
  await page.fill("#m-why", "Scale retail + B2B");
  await page.fill("#m-agenda", "Omnichannel data + support");
  await page.screenshot({ path: `${SHOTS}/02-dialog.png` });
  await page.getByRole("button", { name: "Create meeting" }).click();

  await expect(page.getByRole("dialog")).toBeHidden();
  await page.goto("/dashboard");
  await expect(page.getByText("The Sleep Company").first()).toBeVisible();
  await expect(page.getByText("Account Executive").first()).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/03-dashboard.png`, fullPage: true });
});

test("brief view renders, toggles personas, and Scout answers", async ({ page }) => {
  const id = await seedMeeting("ae");
  await page.goto(`/meeting/${id}`);

  // AE brief
  await expect(page.getByRole("heading", { name: "The Sleep Company", level: 1 })).toBeVisible();
  await expect(page.getByText("Account Executive · Pre-Call Brief")).toBeVisible();
  await expect(page.getByText("ARR")).toBeVisible();          // KPI strip
  await expect(page.getByText("₹700 Cr")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Pain Hypotheses/ })).toBeVisible(); // an AE section
  await expect(page.getByText(/Ready · \d+ source/)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/04-brief-ae.png`, fullPage: true });

  // Toggle → SDR (distinct section set)
  await page.getByRole("tab", { name: "Sales Development Rep" }).click();
  await expect(page.getByRole("heading", { name: "Ready-to-Send Opener" })).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: `${SHOTS}/05-brief-sdr.png`, fullPage: true });

  // Toggle → SE
  await page.getByRole("tab", { name: "Solutions Engineer" }).click();
  await expect(page.getByRole("heading", { name: /Demo Focus/ })).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: `${SHOTS}/06-brief-se.png`, fullPage: true });

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

  // Sync the (mock) calendar → the Sleep Company event imports.
  await page.getByRole("button", { name: /Sync calendar now/i }).click();
  await expect(page.getByText(/imported 1 prospect meeting/i)).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: `${SHOTS}/11-settings-synced.png`, fullPage: true });
});

test("send-as-email composes a persona digest and demo-sends", async ({ page }) => {
  const id = await seedMeeting("ae");
  await page.goto(`/meeting/${id}`);
  await expect(page.getByRole("heading", { name: "The Sleep Company", level: 1 })).toBeVisible();

  // Open the email dialog from the brief toolbar.
  await page.getByRole("button", { name: /send as email/i }).click();
  const dialog = page.getByRole("dialog", { name: /send brief as email/i });
  await expect(dialog).toBeVisible();

  // Recipient prefilled, subject + attachment composed, preview rendered.
  await expect(dialog.getByLabel("To")).not.toHaveValue("");
  await expect(dialog.getByText(/Account Executive Brief/)).toBeVisible({ timeout: 20_000 });
  await expect(dialog.getByText(/-ae-brief\.html/)).toBeVisible();
  await expect(dialog.getByText(/Demo mode/)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/08-email-dialog.png`, fullPage: true });

  // Confirm → demo-send success.
  await dialog.getByRole("button", { name: /confirm send/i }).click();
  await expect(page.getByText(/Demo send complete/)).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: `${SHOTS}/09-email-sent.png`, fullPage: true });
});
