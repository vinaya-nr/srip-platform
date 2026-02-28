"use client";

import { create } from "zustand";

type CartLine = {
  productId: string;
  name: string;
  unitPrice: number;
  quantity: number;
};

type CartState = {
  items: CartLine[];
  addItem: (item: Omit<CartLine, "quantity">) => void;
  updateQty: (productId: string, quantity: number) => void;
  removeItem: (productId: string) => void;
  clear: () => void;
};

// MVP: memory-only cart. Phase 2 can add sessionStorage persistence.
export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  addItem: (item) => {
    const current = get().items;
    const existing = current.find((line) => line.productId === item.productId);
    if (existing) {
      set({
        items: current.map((line) =>
          line.productId === item.productId ? { ...line, quantity: line.quantity + 1 } : line
        )
      });
      return;
    }
    set({ items: [...current, { ...item, quantity: 1 }] });
  },
  updateQty: (productId, quantity) =>
    set({
      items:
        quantity <= 0
          ? get().items.filter((line) => line.productId !== productId)
          : get().items.map((line) => (line.productId === productId ? { ...line, quantity } : line))
    }),
  removeItem: (productId) => set({ items: get().items.filter((line) => line.productId !== productId) }),
  clear: () => set({ items: [] })
}));
