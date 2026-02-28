import { expect, Page } from "@playwright/test";

export class DashboardPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto("/dashboard");
    await expect(this.page.getByTestId("dashboard-page")).toBeVisible();
  }

  async expectSummaryCards() {
    await expect(this.page.getByTestId("summary-today-sales")).toBeVisible();
    await expect(this.page.getByTestId("summary-today-revenue")).toBeVisible();
    await expect(this.page.getByTestId("summary-active-products")).toBeVisible();
    await expect(this.page.getByTestId("summary-low-stock")).toBeVisible();
    await expect(this.page.getByTestId("summary-unread-notifications")).toBeVisible();
  }
}
