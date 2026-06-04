import { test, expect } from "@playwright/test";

/**
 * Agency Tier Onboarding E2E Tests
 * 
 * These tests cover the complete agency onboarding flow:
 * 1. Create organization
 * 2. Create first workspace
 * 3. Invite team members
 * 4. Set up white-label branding
 * 5. Create and analyze competitor
 * 6. Run content prediction
 * 7. Set up approval workflow
 * 8. Generate and download report
 */

test.describe("Agency Onboarding Flow", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate and login
    await page.goto("/login");
    // Note: In real tests, use proper test credentials or mock auth
  });

  test("complete agency onboarding flow", async ({ page }) => {
    // Step 1: Navigate to organizations
    await page.goto("/organizations");
    
    // Create organization
    await page.click("[data-testid='create-organization-button']");
    await page.fill("[data-testid='org-name-input']", "Test Agency");
    await page.fill("[data-testid='org-slug-input']", "test-agency-" + Date.now());
    await page.click("[data-testid='create-org-submit']");
    
    // Verify organization created
    await expect(page.locator("[data-testid='organization-card']")).toBeVisible();
    
    // Step 2: Create workspace
    await page.click("[data-testid='create-workspace-button']");
    await page.fill("[data-testid='workspace-name-input']", "Client A");
    await page.fill("[data-testid='workspace-slug-input']", "client-a");
    await page.fill("[data-testid='client-name-input']", "Acme Corporation");
    await page.click("[data-testid='create-workspace-submit']");
    
    // Verify workspace created
    await expect(page.locator("[data-testid='workspace-card']")).toContainText("Client A");
    
    // Step 3: Test workspace switcher
    await page.click("[data-testid='workspace-switcher-trigger']");
    await expect(page.locator("[data-testid='workspace-dropdown']")).toBeVisible();
    
    // Step 4: Navigate to predictions
    await page.goto("/predictions");
    
    // Enter content for prediction
    await page.fill(
      "[data-testid='prediction-content-input']",
      "Excited to announce our new AI-powered content strategy platform! " +
      "#ContentStrategy #AI #Marketing"
    );
    await page.selectOption("[data-testid='platform-select']", "linkedin");
    
    // Submit prediction
    await page.click("[data-testid='analyze-content-button']");
    
    // Wait for prediction results
    await expect(page.locator("[data-testid='prediction-results']")).toBeVisible({ timeout: 30000 });
    
    // Verify prediction tabs exist
    await expect(page.locator("[data-testid='performance-tab']")).toBeVisible();
    await expect(page.locator("[data-testid='viral-tab']")).toBeVisible();
    await expect(page.locator("[data-testid='timing-tab']")).toBeVisible();
    
    // Step 5: Navigate to competitors
    await page.goto("/competitors");
    
    // Add competitor
    await page.click("[data-testid='add-competitor-button']");
    await page.fill("[data-testid='competitor-name-input']", "HubSpot");
    await page.fill("[data-testid='competitor-handle-input']", "hubspot");
    await page.selectOption("[data-testid='competitor-platform-select']", "linkedin");
    await page.click("[data-testid='add-competitor-submit']");
    
    // Verify competitor added
    await expect(page.locator("[data-testid='competitor-card']")).toContainText("HubSpot");
    
    // Step 6: Set up approval workflow
    await page.goto("/approvals/workflows");
    
    await page.click("[data-testid='create-workflow-button']");
    await page.fill("[data-testid='workflow-name-input']", "Standard Review");
    await page.selectOption("[data-testid='content-type-select']", "post");
    
    // Add workflow step
    await page.click("[data-testid='add-step-button']");
    await page.fill("[data-testid='step-title-input']", "Manager Review");
    await page.selectOption("[data-testid='step-role-select']", "manager");
    await page.click("[data-testid='save-step-button']");
    
    // Save workflow
    await page.click("[data-testid='save-workflow-button']");
    
    // Verify workflow created
    await expect(page.locator("[data-testid='workflow-card']")).toContainText("Standard Review");
    
    // Step 7: Generate report
    await page.goto("/reports");
    
    await page.click("[data-testid='generate-analytics-report']");
    await page.selectOption("[data-testid='report-period-select']", "30");
    await page.click("[data-testid='generate-report-submit']");
    
    // Wait for report generation
    await expect(page.locator("[data-testid='report-download-link']")).toBeVisible({ timeout: 60000 });
    
    // Verify download link
    const downloadLink = await page.locator("[data-testid='report-download-link']").getAttribute("href");
    expect(downloadLink).toContain("/api/v1/reports/download/");
  });

  test("workspace permission-based feature gating", async ({ page }) => {
    // Login as editor role user
    // Navigate to predictions (should be accessible)
    await page.goto("/predictions");
    await expect(page.locator("[data-testid='predictions-page']")).toBeVisible();
    
    // Try to access organization settings (should be restricted)
    await page.goto("/organizations/settings");
    await expect(page.locator("[data-testid='access-denied']")).toBeVisible();
    
    // Try to access reports (should be accessible for editor)
    await page.goto("/reports");
    await expect(page.locator("[data-testid='reports-page']")).toBeVisible();
  });

  test("white-label settings configuration", async ({ page }) => {
    // Login as admin
    await page.goto("/settings/white-label");
    
    // Enable white-label
    await page.click("[data-testid='enable-white-label-toggle']");
    
    // Set brand color
    await page.fill("[data-testid='primary-color-input']", "#FF5733");
    
    // Set custom footer
    await page.fill(
      "[data-testid='custom-footer-input']",
      "© 2025 Test Agency. All rights reserved."
    );
    
    // Hide powered by
    await page.click("[data-testid='hide-powered-by-toggle']");
    
    // Save settings
    await page.click("[data-testid='save-white-label-settings']");
    
    // Verify saved
    await expect(page.locator("[data-testid='settings-saved-toast']")).toBeVisible();
    
    // Generate report and verify branding
    await page.goto("/reports");
    await page.click("[data-testid='generate-analytics-report']");
    
    // Download and verify (in real test, would verify PDF contents)
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("[data-testid='report-download-link']"),
    ]);
    
    expect(download.suggestedFilename()).toContain("report_");
  });
});

test.describe("Agency Multi-Client Features", () => {
  test("switch between client workspaces", async ({ page }) => {
    await page.goto("/dashboard");
    
    // Open workspace switcher
    await page.click("[data-testid='workspace-switcher-trigger']");
    
    // Verify multiple workspaces shown
    const workspaces = await page.locator("[data-testid='workspace-option']").count();
    expect(workspaces).toBeGreaterThan(1);
    
    // Switch to second workspace
    await page.click("[data-testid='workspace-option']:nth-child(2)");
    
    // Verify context changed
    await expect(page.locator("[data-testid='current-workspace-name']")).toHaveText(/Client/);
  });

  test("competitor analysis and gap detection", async ({ page }) => {
    await page.goto("/competitors");
    
    // Add competitor
    await page.click("[data-testid='add-competitor-button']");
    await page.fill("[data-testid='competitor-name-input']", "Competitor A");
    await page.fill("[data-testid='competitor-handle-input']", "competitor_a");
    await page.selectOption("[data-testid='competitor-platform-select']", "linkedin");
    await page.click("[data-testid='add-competitor-submit']");
    
    // Wait for competitor card
    await expect(page.locator("[data-testid='competitor-card']")).toBeVisible();
    
    // Run strategy analysis
    await page.click("[data-testid='analyze-strategy-button']");
    
    // Wait for analysis results
    await expect(page.locator("[data-testid='strategy-analysis-results']")).toBeVisible({ timeout: 30000 });
    
    // Navigate to gaps tab
    await page.click("[data-testid='gaps-tab']");
    
    // Run gap analysis
    await page.click("[data-testid='analyze-gaps-button']");
    
    // Wait for gap analysis results
    await expect(page.locator("[data-testid='gap-analysis-results']")).toBeVisible({ timeout: 30000 });
    
    // Verify gap topics shown
    await expect(page.locator("[data-testid='gap-topic-card']")).toBeVisible();
  });
});

test.describe("Smart Scheduler Integration", () => {
  test("AI-suggested optimal posting time", async ({ page }) => {
    await page.goto("/content/drafts");
    
    // Create new draft
    await page.click("[data-testid='create-draft-button']");
    await page.fill(
      "[data-testid='draft-content-input']",
      "Testing AI-powered optimal timing suggestions!"
    );
    await page.selectOption("[data-testid='draft-platform-select']", "linkedin");
    await page.click("[data-testid='save-draft-button']");
    
    // Get AI timing suggestion
    await page.click("[data-testid='schedule-button']");
    await page.click("[data-testid='get-ai-timing-suggestion']");
    
    // Wait for suggestion
    await expect(page.locator("[data-testid='ai-timing-suggestion']")).toBeVisible({ timeout: 30000 });
    
    // Verify confidence score shown
    await expect(page.locator("[data-testid='timing-confidence-score']")).toBeVisible();
    
    // Apply suggestion
    await page.click("[data-testid='apply-suggested-time']");
    
    // Verify scheduled
    await expect(page.locator("[data-testid='draft-status']")).toContainText("Scheduled");
  });
});

test.describe("Approval Workflow Integration", () => {
  test("content approval workflow", async ({ page }) => {
    // As content creator
    await page.goto("/content/drafts");
    
    // Create draft
    await page.click("[data-testid='create-draft-button']");
    await page.fill(
      "[data-testid='draft-content-input']",
      "This content needs approval before publishing!"
    );
    await page.click("[data-testid='request-approval-button']");
    
    // Select workflow
    await page.selectOption("[data-testid='workflow-select']", "standard-review");
    await page.click("[data-testid='submit-approval-request']");
    
    // Verify pending status
    await expect(page.locator("[data-testid='draft-status']")).toContainText("Pending Approval");
    
    // Switch to approver account
    // (In real test, would login as different user or use API to simulate)
    
    // Navigate to pending approvals
    await page.goto("/approvals/pending");
    
    // Verify approval request shown
    await expect(page.locator("[data-testid='approval-request-card']")).toBeVisible();
    
    // Approve content
    await page.click("[data-testid='approve-button']");
    await page.fill("[data-testid='approval-comments-input']", "Looks good!");
    await page.click("[data-testid='submit-approval-button']");
    
    // Verify approved
    await expect(page.locator("[data-testid='approval-status']")).toContainText("Approved");
  });
});
