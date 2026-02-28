import { describe, expect, it } from "vitest";

import { formatMoney } from "@/lib/money";

describe("formatMoney", () => {
  it("formats INR values with Rs prefix and indian locale", () => {
    expect(formatMoney(1234.5, "INR")).toBe("Rs 1,234.50");
    expect(formatMoney("1000000", "INR")).toBe("Rs 10,00,000.00");
  });

  it("formats non-INR values using Intl currency format", () => {
    expect(formatMoney(12.5, "USD")).toBe("$12.50");
    expect(formatMoney("25", "EUR")).toBe("€25.00");
  });

  it("falls back to 0 for null, undefined, NaN, and non-numeric strings", () => {
    expect(formatMoney(null, "INR")).toBe("Rs 0.00");
    expect(formatMoney(undefined, "USD")).toBe("$0.00");
    expect(formatMoney(Number.NaN, "INR")).toBe("Rs 0.00");
    expect(formatMoney("abc", "USD")).toBe("$0.00");
  });
});

