export type User = {
  id: string;
  email: string;
  shop_id: string;
};

export type ShopProfile = {
  id: string;
  name: string;
  created_at: string;
};

export type UserProfile = {
  user: User & {
    is_active: boolean;
    created_at: string;
  };
  shop: ShopProfile;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
};

export type Paged<T> = {
  items: T[];
  total: number;
  skip: number;
  limit: number;
};

export type Product = {
  id: string;
  shop_id: string;
  category_id: string | null;
  name: string;
  sku: string;
  description: string | null;
  price: string;
  low_stock_threshold: number;
  is_active: boolean;
};

export type Category = {
  id: string;
  shop_id: string;
  name: string;
  created_at: string;
};

export type Batch = {
  id: string;
  shop_id: string;
  product_id: string;
  quantity: number;
  unit_cost: string | null;
  expiry_date: string | null;
};

export type SaleItem = {
  product_id: string;
  product_name?: string | null;
  quantity: number;
  unit_price: string;
  line_total: string;
};

export type Sale = {
  id: string;
  shop_id: string;
  sale_number: string;
  total_amount: string;
  created_at: string;
  items: SaleItem[];
};

export type Notification = {
  id: string;
  shop_id: string;
  event_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

export type DashboardSummary = {
  today_sales_total: number;
  today_revenue_total: string;
  active_products_count: number;
  low_stock_count: number;
  unread_notifications_count: number;
};

export type Snapshot = {
  id: string;
  shop_id: string;
  snapshot_type: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type TopProductPoint = {
  product_id: string;
  product_name: string;
  total_quantity: number;
  total_revenue: number;
};

export type RevenueSeriesPoint = {
  bucket: string;
  total_revenue: number;
  total_sales: number;
};

export type MonthlyComparisonPoint = {
  month: string;
  total_revenue: number;
  total_sales: number;
};

export type RevenueProfitSummary = {
  total_revenue: number;
  total_profit: number;
  total_cogs: number;
};

export type ApiError = {
  success?: false;
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
    correlation_id?: string;
    timestamp?: string;
  };
};
