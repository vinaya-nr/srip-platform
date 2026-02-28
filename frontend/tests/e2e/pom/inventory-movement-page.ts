import { expect, Page } from "@playwright/test";

export class InventoryMovementPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto("/inventory/movements/new");
    await expect(this.page.getByTestId("movement-form")).toBeVisible();
  }

  async submitMovement(payload: {
    productId: string;
    batchId?: string;
    movementType: "in" | "out" | "adjustment";
    quantity: number;
    adjustmentMode?: "increase" | "decrease";
    reason?: string;
  }) {
    await this.page.getByTestId("movement-product-id").selectOption(payload.productId);
    if (payload.batchId) {
      await this.page.getByTestId("movement-batch-id").selectOption(payload.batchId);
    } else {
      await this.page.getByTestId("movement-batch-id").selectOption({ index: 1 });
    }
    await this.page.getByTestId("movement-type").selectOption(payload.movementType);
    if (payload.movementType === "adjustment" && payload.adjustmentMode) {
      await this.page.getByTestId("movement-adjustment-mode").selectOption(payload.adjustmentMode);
    }
    await this.page.getByTestId("movement-quantity").fill(String(payload.quantity));
    if (payload.reason) {
      await this.page.getByTestId("movement-reason").fill(payload.reason);
    }
    await this.page.getByTestId("movement-submit").click();
    await expect(this.page).toHaveURL(/\/inventory$/);
  }
}
