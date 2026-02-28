import { APIRequestContext, APIResponse, expect } from "@playwright/test";

import { E2E_API_BASE_URL } from "./constants";
import { assertSafeE2EApiBaseUrl } from "./safety";
import type { Category, LoginResponse, Notification, Paged, Product, Snapshot } from "./types";

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

export class SripApiClient {
  constructor(
    private readonly request: APIRequestContext,
    private readonly baseUrl: string = E2E_API_BASE_URL
  ) {
    assertSafeE2EApiBaseUrl();
  }

  private async call<T>(
    method: HttpMethod,
    path: string,
    token?: string,
    data?: unknown
  ): Promise<T> {
    const response = await this.request.fetch(`${this.baseUrl}${path}`, {
      method,
      data,
      headers: token ? { Authorization: `Bearer ${token}` } : undefined
    });
    return this.assertAndParse<T>(response);
  }

  private async assertAndParse<T>(response: APIResponse): Promise<T> {
    const responseText = await response.text();
    expect(response.ok(), `API failure [${response.status()}]: ${responseText}`).toBeTruthy();
    if (!responseText) {
      return undefined as T;
    }
    return JSON.parse(responseText) as T;
  }

  async register(email: string, password: string, shopName: string): Promise<void> {
    await this.call("POST", "/users", undefined, { email, password, shop_name: shopName });
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    return this.call<LoginResponse>("POST", "/auth/login", undefined, { email, password });
  }

  async refresh(): Promise<LoginResponse> {
    return this.call<LoginResponse>("POST", "/auth/refresh");
  }

  async createCategory(token: string, name: string): Promise<Category> {
    return this.call<Category>("POST", "/categories", token, { name });
  }

  async listCategories(token: string): Promise<Category[]> {
    return this.call<Category[]>("GET", "/categories", token);
  }

  async updateCategory(token: string, categoryId: string, name: string): Promise<Category> {
    return this.call<Category>("PATCH", `/categories/${categoryId}`, token, { name });
  }

  async deleteCategory(token: string, categoryId: string): Promise<void> {
    await this.call("DELETE", `/categories/${categoryId}`, token);
  }

  async createProduct(
    token: string,
    payload: {
      category_id: string;
      name: string;
      sku: string;
      description?: string | null;
      price: number;
      low_stock_threshold?: number;
    }
  ): Promise<Product> {
    return this.call<Product>("POST", "/products", token, payload);
  }

  async listProducts(
    token: string,
    query: { search?: string; categoryId?: string; skip?: number; limit?: number } = {}
  ): Promise<Paged<Product>> {
    const params = new URLSearchParams();
    if (query.search) params.set("search", query.search);
    if (query.categoryId) params.set("category_id", query.categoryId);
    params.set("skip", String(query.skip ?? 0));
    params.set("limit", String(query.limit ?? 20));
    return this.call<Paged<Product>>("GET", `/products?${params.toString()}`, token);
  }

  async updateProduct(
    token: string,
    productId: string,
    payload: Partial<{
      category_id: string | null;
      name: string;
      sku: string;
      description: string | null;
      price: number;
      low_stock_threshold: number;
      is_active: boolean;
    }>
  ): Promise<Product> {
    return this.call<Product>("PATCH", `/products/${productId}`, token, payload);
  }

  async deleteProduct(token: string, productId: string): Promise<void> {
    await this.call("DELETE", `/products/${productId}`, token);
  }

  async createBatch(
    token: string,
    payload: { product_id: string; quantity: number; unit_cost?: number; expiry_date?: string }
  ): Promise<void> {
    await this.call("POST", "/inventory/batches", token, payload);
  }

  async createMovement(
    token: string,
    payload: {
      product_id: string;
      batch_id: string;
      movement_type: "in" | "out" | "adjustment";
      quantity: number;
      adjustment_mode?: "increase" | "decrease";
      reason?: string;
      unit_cost?: number;
    }
  ): Promise<void> {
    await this.call("POST", "/inventory/movements", token, payload);
  }

  async getProductStock(token: string, productId: string): Promise<{ current_stock: number }> {
    return this.call<{ current_stock: number }>("GET", `/products/${productId}/stock`, token);
  }

  async createSale(token: string, items: { product_id: string; quantity: number }[]) {
    return this.call("POST", "/sales", token, { items });
  }

  async createNotification(token: string, payload: { event_type: string; title: string; message: string }) {
    return this.call<Notification>("POST", "/notifications", token, payload);
  }

  async listNotifications(token: string, unreadOnly = false): Promise<Paged<Notification>> {
    return this.call<Paged<Notification>>("GET", `/notifications?unread_only=${String(unreadOnly)}`, token);
  }

  async markNotificationRead(token: string, notificationId: string) {
    return this.call<Notification>("PATCH", `/notifications/${notificationId}/read`, token);
  }

  async listSnapshots(token: string): Promise<Snapshot[]> {
    return this.call<Snapshot[]>("GET", "/analytics/snapshots", token);
  }

  async createSnapshot(
    token: string,
    payload: { snapshot_type: string; payload: Record<string, unknown> }
  ): Promise<Snapshot> {
    return this.call<Snapshot>("POST", "/analytics/snapshots", token, payload);
  }
}
