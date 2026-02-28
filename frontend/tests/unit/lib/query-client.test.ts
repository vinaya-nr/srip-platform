import { describe, expect, it } from "vitest";

import { queryClient } from "@/lib/query-client";

describe("queryClient", () => {
  it("uses expected default query options", () => {
    const defaults = queryClient.getDefaultOptions();
    expect(defaults.queries?.retry).toBe(1);
    expect(defaults.queries?.refetchOnWindowFocus).toBe(false);
  });
});
