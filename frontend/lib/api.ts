import { apiRequest } from "./http";
import type {
  Batch,
  Category,
  DashboardSummary,
  Notification,
  RevenueProfitSummary,
  Paged,
  Product,
  MonthlyComparisonPoint,
  Sale,
  RevenueSeriesPoint,
  Snapshot,
  TopProductPoint,
  TokenResponse,
  UserProfile
} from "./types";

export function login(payload: { email: string; password: string }) {
  return apiRequest<TokenResponse>("/auth/login", { method: "POST", body: payload });
}

export function register(payload: { email: string; password: string; shop_name: string }) {
  return apiRequest("/users", { method: "POST", body: payload });
}

export function getMyProfile(token: string) {
  return apiRequest<UserProfile>("/users/me", { token });
}

export function logout(token: string | null) {
  return apiRequest("/auth/logout", { method: "POST", token });
}

export function getDashboardSummary(token: string) {
  return apiRequest<DashboardSummary>("/dashboard/summary", { token });
}

export function getProducts(token: string, skip = 0, limit = 20) {
  return apiRequest<Paged<Product>>(`/products?skip=${skip}&limit=${limit}`, { token });
}

export function getCategories(token: string) {
  return apiRequest<Category[]>("/categories", { token });
}

export function createCategory(token: string, payload: { name: string }) {
  return apiRequest<Category>("/categories", { method: "POST", token, body: payload });
}

export function updateCategory(token: string, categoryId: string, payload: { name: string }) {
  return apiRequest<Category>(`/categories/${categoryId}`, { method: "PATCH", token, body: payload });
}

export function deleteCategory(token: string, categoryId: string) {
  return apiRequest<void>(`/categories/${categoryId}`, { method: "DELETE", token });
}

export function getProductsWithFilters(
  token: string,
  options: {
    skip?: number;
    limit?: number;
    search?: string;
    categoryId?: string;
    isActive?: boolean;
  } = {}
) {
  const params = new URLSearchParams();
  params.set("skip", String(options.skip ?? 0));
  params.set("limit", String(options.limit ?? 20));
  if (options.search?.trim()) {
    params.set("search", options.search.trim());
  }
  if (options.categoryId?.trim()) {
    params.set("category_id", options.categoryId.trim());
  }
  if (options.isActive !== undefined) {
    params.set("is_active", String(options.isActive));
  }
  return apiRequest<Paged<Product>>(`/products?${params.toString()}`, { token });
}

export function createProduct(
  token: string,
  payload: {
    category_id: string;
    name: string;
    sku: string;
    description?: string | null;
    price: number;
    low_stock_threshold?: number;
  }
) {
  return apiRequest<Product>("/products", { method: "POST", token, body: payload });
}

export function updateProduct(
  token: string,
  productId: string,
  payload: {
    category_id?: string | null;
    name?: string;
    sku?: string;
    description?: string | null;
    price?: number;
    low_stock_threshold?: number;
    is_active?: boolean;
  }
) {
  return apiRequest<Product>(`/products/${productId}`, { method: "PATCH", token, body: payload });
}

export function deleteProduct(token: string, productId: string) {
  return apiRequest<void>(`/products/${productId}`, { method: "DELETE", token });
}

export function getSales(
  token: string,
  skip = 0,
  limit = 20,
  options: {
    fromDate?: string;
    toDate?: string;
  } = {}
) {
  const params = new URLSearchParams();
  params.set("skip", String(skip));
  params.set("limit", String(limit));
  if (options.fromDate) {
    params.set("from_date", options.fromDate);
  }
  if (options.toDate) {
    params.set("to_date", options.toDate);
  }
  return apiRequest<Paged<Sale>>(`/sales?${params.toString()}`, { token });
}

export function getSale(token: string, saleId: string) {
  return apiRequest<Sale>(`/sales/${saleId}`, { token });
}

export function getSnapshots(token: string, snapshotType?: string) {
  const query = snapshotType ? `?snapshot_type=${encodeURIComponent(snapshotType)}` : "";
  return apiRequest<Snapshot[]>(`/analytics/snapshots${query}`, { token });
}

export function getTopProducts(
  token: string,
  options: {
    fromDate: string;
    toDate: string;
    limit?: number;
  }
) {
  const params = new URLSearchParams();
  params.set("from_date", options.fromDate);
  params.set("to_date", options.toDate);
  params.set("limit", String(options.limit ?? 5));
  return apiRequest<TopProductPoint[]>(`/analytics/top-products?${params.toString()}`, { token });
}

export function getRevenueSeries(
  token: string,
  options: {
    fromDate: string;
    toDate: string;
    bucket?: "day" | "hour";
  }
) {
  const params = new URLSearchParams();
  params.set("from_date", options.fromDate);
  params.set("to_date", options.toDate);
  params.set("bucket", options.bucket ?? "day");
  return apiRequest<RevenueSeriesPoint[]>(`/analytics/revenue-series?${params.toString()}`, { token });
}

export function getRevenueProfitSummary(
  token: string,
  options: {
    fromDate: string;
    toDate: string;
  }
) {
  const params = new URLSearchParams();
  params.set("from_date", options.fromDate);
  params.set("to_date", options.toDate);
  return apiRequest<RevenueProfitSummary>(`/analytics/revenue-profit-summary?${params.toString()}`, { token });
}

export function getMonthlyComparison(token: string, months = 6) {
  return apiRequest<MonthlyComparisonPoint[]>(`/analytics/monthly-comparison?months=${months}`, { token });
}

export function getNotifications(
  token: string,
  skip = 0,
  limit = 20,
  options: {
    fromDate?: string;
    toDate?: string;
  } = {}
) {
  const params = new URLSearchParams();
  params.set("skip", String(skip));
  params.set("limit", String(limit));
  if (options.fromDate) {
    params.set("from_date", options.fromDate);
  }
  if (options.toDate) {
    params.set("to_date", options.toDate);
  }
  return apiRequest<Paged<Notification>>(`/notifications?${params.toString()}`, { token });
}

export function markNotificationRead(token: string, notificationId: string) {
  return apiRequest<Notification>(`/notifications/${notificationId}/read`, { method: "PATCH", token });
}

export function getBatches(token: string, skip = 0, limit = 20, productId?: string) {
  const productFilter = productId ? `&product_id=${encodeURIComponent(productId)}` : "";
  return apiRequest<Paged<Batch>>(`/inventory/batches?skip=${skip}&limit=${limit}${productFilter}`, { token });
}

export function createBatch(
  token: string,
  payload: {
    product_id: string;
    quantity: number;
    unit_cost?: number;
    expiry_date?: string;
  }
) {
  return apiRequest<Batch>("/inventory/batches", { method: "POST", token, body: payload });
}

export function updateBatch(
  token: string,
  batchId: string,
  payload: {
    unit_cost?: number | null;
    expiry_date?: string | null;
  }
) {
  return apiRequest<Batch>(`/inventory/batches/${batchId}`, { method: "PATCH", token, body: payload });
}

export function createMovement(
  token: string,
  payload: {
    product_id: string;
    batch_id: string;
    movement_type: "in" | "out" | "adjustment";
    quantity: number;
    adjustment_mode?: "increase" | "decrease";
    unit_cost?: number;
    expiry_date?: string;
    reason?: string;
  }
) {
  return apiRequest("/inventory/movements", { method: "POST", token, body: payload });
}

export function createSale(token: string, payload: { items: { product_id: string; quantity: number }[] }) {
  return apiRequest<Sale>("/sales", { method: "POST", token, body: payload });
}

export function getProductStock(token: string, productId: string) {
  return apiRequest<{ product_id: string; shop_id: string; current_stock: number }>(`/products/${productId}/stock`, {
    token
  });
}
