import { describe, expect, it } from "vitest";

import { useCartStore } from "@/stores/cart-store";

describe("cart store", () => {
  it("adds items and increments quantity for same product", () => {
    useCartStore.getState().clear();
    useCartStore.getState().addItem({ productId: "p0", name: "Prod0", unitPrice: 8 });
    useCartStore.getState().addItem({ productId: "p1", name: "Prod1", unitPrice: 10 });
    useCartStore.getState().addItem({ productId: "p1", name: "Prod1", unitPrice: 10 });

    const items = useCartStore.getState().items;
    expect(items).toHaveLength(2);
    expect(items.find((x) => x.productId === "p1")?.quantity).toBe(2);
    expect(items.find((x) => x.productId === "p0")?.quantity).toBe(1);
  });

  it("updates quantity and removes item when quantity <= 0", () => {
    useCartStore.getState().clear();
    useCartStore.getState().addItem({ productId: "p2", name: "Prod2", unitPrice: 15 });
    useCartStore.getState().updateQty("p2", 4);
    expect(useCartStore.getState().items[0].quantity).toBe(4);

    useCartStore.getState().updateQty("p2", 0);
    expect(useCartStore.getState().items).toHaveLength(0);
  });

  it("removes and clears items", () => {
    useCartStore.getState().clear();
    useCartStore.getState().addItem({ productId: "p3", name: "Prod3", unitPrice: 20 });
    useCartStore.getState().removeItem("p3");
    expect(useCartStore.getState().items).toHaveLength(0);

    useCartStore.getState().addItem({ productId: "p4", name: "Prod4", unitPrice: 22 });
    useCartStore.getState().clear();
    expect(useCartStore.getState().items).toHaveLength(0);
  });

  it("keeps non-target lines unchanged when updating or removing", () => {
    useCartStore.getState().clear();
    useCartStore.getState().addItem({ productId: "p5", name: "Prod5", unitPrice: 30 });
    useCartStore.getState().addItem({ productId: "p6", name: "Prod6", unitPrice: 40 });

    useCartStore.getState().updateQty("p5", 3);
    const afterUpdate = useCartStore.getState().items;
    expect(afterUpdate.find((x) => x.productId === "p5")?.quantity).toBe(3);
    expect(afterUpdate.find((x) => x.productId === "p6")?.quantity).toBe(1);

    useCartStore.getState().removeItem("missing-id");
    expect(useCartStore.getState().items).toHaveLength(2);
  });
});
