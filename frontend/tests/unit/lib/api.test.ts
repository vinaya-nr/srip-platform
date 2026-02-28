import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/http", () => ({
  apiRequest: vi.fn()
}));

import { apiRequest } from "@/lib/http";
import {
  createBatch,
  createCategory,
  createMovement,
  createProduct,
  createSale,
  deleteCategory,
  deleteProduct,
  getDashboardSummary,
  getBatches,
  getCategories,
  getNotifications,
  getMonthlyComparison,
  getMyProfile,
  getProductStock,
  getProducts,
  getProductsWithFilters,
  getRevenueSeries,
  getRevenueProfitSummary,
  getSale,
  getSales,
  getSnapshots,
  getTopProducts,
  login,
  logout,
  markNotificationRead,
  register,
  updateBatch,
  updateCategory,
  updateProduct
} from "@/lib/api";

describe("API wrappers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls auth endpoints", () => {
    login({ email: "u@x.com", password: "p" });
    register({ email: "u@x.com", password: "p", shop_name: "shop" });
    getMyProfile("token");
    logout("token");
    expect(apiRequest).toHaveBeenCalledTimes(4);
  });

  it("builds product and sales listing queries", () => {
    getProducts("tok", 20, 10);
    getSales("tok", 0, 20);
    getSale("tok", "sale-1");
    expect(apiRequest).toHaveBeenCalledWith("/products?skip=20&limit=10", { token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/sales?skip=0&limit=20", { token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/sales/sale-1", { token: "tok" });
  });

  it("uses default pagination for product and sales listing queries", () => {
    getProducts("tok");
    getSales("tok");
    expect(apiRequest).toHaveBeenCalledWith("/products?skip=0&limit=20", { token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/sales?skip=0&limit=20", { token: "tok" });
  });

  it("builds filtered products query", () => {
    getProductsWithFilters("tok", { search: "abc", categoryId: "c1", isActive: false, skip: 0, limit: 5 });
    expect(apiRequest).toHaveBeenCalledWith(
      "/products?skip=0&limit=5&search=abc&category_id=c1&is_active=false",
      { token: "tok" }
    );
  });

  it("builds default products filter query when no options are passed", () => {
    getProductsWithFilters("tok");
    expect(apiRequest).toHaveBeenCalledWith("/products?skip=0&limit=20", { token: "tok" });
  });

  it("trims search/category and omits blank values", () => {
    getProductsWithFilters("tok", {
      search: "   ",
      categoryId: "  ",
      isActive: true,
      skip: 1,
      limit: 10
    });
    expect(apiRequest).toHaveBeenCalledWith("/products?skip=1&limit=10&is_active=true", { token: "tok" });
  });

  it("handles categories CRUD wrappers", () => {
    getCategories("tok");
    createCategory("tok", { name: "Cat" });
    updateCategory("tok", "c1", { name: "Cat2" });
    deleteCategory("tok", "c1");
    expect(apiRequest).toHaveBeenCalledWith("/categories", { token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/categories", { method: "POST", token: "tok", body: { name: "Cat" } });
    expect(apiRequest).toHaveBeenCalledWith("/categories/c1", { method: "PATCH", token: "tok", body: { name: "Cat2" } });
    expect(apiRequest).toHaveBeenCalledWith("/categories/c1", { method: "DELETE", token: "tok" });
  });

  it("handles products CRUD wrappers", () => {
    createProduct("tok", { category_id: "cat-1", name: "P", sku: "S", price: 10 });
    updateProduct("tok", "p1", { name: "P2" });
    deleteProduct("tok", "p1");
    expect(apiRequest).toHaveBeenCalledWith("/products", expect.objectContaining({ method: "POST" }));
    expect(apiRequest).toHaveBeenCalledWith("/products/p1", expect.objectContaining({ method: "PATCH" }));
    expect(apiRequest).toHaveBeenCalledWith("/products/p1", expect.objectContaining({ method: "DELETE" }));
  });

  it("handles inventory and notification wrappers", () => {
    getBatches("tok", 0, 20, "p1");
    createBatch("tok", { product_id: "p1", quantity: 10 });
    updateBatch("tok", "b1", { unit_cost: 3.5, expiry_date: "2031-01-01" });
    createMovement("tok", { product_id: "p1", batch_id: "b1", movement_type: "in", quantity: 2 });
    getNotifications("tok", 0, 10);
    markNotificationRead("tok", "n1");
    expect(apiRequest).toHaveBeenCalledWith("/inventory/batches?skip=0&limit=20&product_id=p1", { token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/inventory/batches", expect.objectContaining({ method: "POST" }));
    expect(apiRequest).toHaveBeenCalledWith("/inventory/batches/b1", expect.objectContaining({ method: "PATCH" }));
    expect(apiRequest).toHaveBeenCalledWith("/inventory/movements", expect.objectContaining({ method: "POST" }));
    expect(apiRequest).toHaveBeenCalledWith("/notifications?skip=0&limit=10", { token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/notifications/n1/read", { method: "PATCH", token: "tok" });
  });

  it("uses default notifications pagination", () => {
    getNotifications("tok");
    expect(apiRequest).toHaveBeenCalledWith("/notifications?skip=0&limit=20", { token: "tok" });
  });

  it("builds notifications query with date range filters", () => {
    getNotifications("tok", 0, 20, { fromDate: "2026-02-01", toDate: "2026-02-26" });
    expect(apiRequest).toHaveBeenCalledWith(
      "/notifications?skip=0&limit=20&from_date=2026-02-01&to_date=2026-02-26",
      { token: "tok" }
    );
  });

  it("builds notifications query with only from-date", () => {
    getNotifications("tok", 2, 10, { fromDate: "2026-02-01" });
    expect(apiRequest).toHaveBeenCalledWith("/notifications?skip=2&limit=10&from_date=2026-02-01", { token: "tok" });
  });

  it("builds notifications query with only to-date", () => {
    getNotifications("tok", 4, 15, { toDate: "2026-02-26" });
    expect(apiRequest).toHaveBeenCalledWith("/notifications?skip=4&limit=15&to_date=2026-02-26", { token: "tok" });
  });

  it("handles snapshots and sales create wrappers", () => {
    getSnapshots("tok", "nightly_snapshot");
    createSale("tok", { items: [{ product_id: "p1", quantity: 1 }] });
    expect(apiRequest).toHaveBeenCalledWith("/analytics/snapshots?snapshot_type=nightly_snapshot", { token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/sales", expect.objectContaining({ method: "POST" }));
  });

  it("builds snapshots query without snapshot type", () => {
    getSnapshots("tok");
    expect(apiRequest).toHaveBeenCalledWith("/analytics/snapshots", { token: "tok" });
  });

  it("builds analytics aggregate queries", () => {
    getTopProducts("tok", { fromDate: "2026-02-01", toDate: "2026-02-25", limit: 5 });
    getRevenueSeries("tok", { fromDate: "2026-02-01", toDate: "2026-02-25", bucket: "day" });
    getRevenueProfitSummary("tok", { fromDate: "2026-02-01", toDate: "2026-02-25" });
    getMonthlyComparison("tok", 6);
    expect(apiRequest).toHaveBeenCalledWith("/analytics/top-products?from_date=2026-02-01&to_date=2026-02-25&limit=5", {
      token: "tok"
    });
    expect(apiRequest).toHaveBeenCalledWith("/analytics/revenue-series?from_date=2026-02-01&to_date=2026-02-25&bucket=day", {
      token: "tok"
    });
    expect(apiRequest).toHaveBeenCalledWith("/analytics/revenue-profit-summary?from_date=2026-02-01&to_date=2026-02-25", {
      token: "tok"
    });
    expect(apiRequest).toHaveBeenCalledWith("/analytics/monthly-comparison?months=6", { token: "tok" });
  });

  it("uses default query params for analytics helpers", () => {
    getTopProducts("tok", { fromDate: "2026-02-01", toDate: "2026-02-25" });
    getRevenueSeries("tok", { fromDate: "2026-02-01", toDate: "2026-02-25" });
    expect(apiRequest).toHaveBeenCalledWith("/analytics/top-products?from_date=2026-02-01&to_date=2026-02-25&limit=5", {
      token: "tok"
    });
    expect(apiRequest).toHaveBeenCalledWith("/analytics/revenue-series?from_date=2026-02-01&to_date=2026-02-25&bucket=day", {
      token: "tok"
    });
  });

  it("builds batches query without product filter", () => {
    getBatches("tok", 5, 15);
    expect(apiRequest).toHaveBeenCalledWith("/inventory/batches?skip=5&limit=15", { token: "tok" });
  });

  it("encodes productId in batch filter query", () => {
    getBatches("tok", 0, 20, "prod/1#x");
    expect(apiRequest).toHaveBeenCalledWith("/inventory/batches?skip=0&limit=20&product_id=prod%2F1%23x", {
      token: "tok"
    });
  });

  it("uses default params for monthly comparison and batches", () => {
    getMonthlyComparison("tok");
    getBatches("tok");
    expect(apiRequest).toHaveBeenCalledWith("/analytics/monthly-comparison?months=6", { token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/inventory/batches?skip=0&limit=20", { token: "tok" });
  });

  it("calls dashboard summary and product stock wrappers", () => {
    getDashboardSummary("tok");
    getProductStock("tok", "p1");
    expect(apiRequest).toHaveBeenCalledWith("/dashboard/summary", { token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/products/p1/stock", { token: "tok" });
  });
});
