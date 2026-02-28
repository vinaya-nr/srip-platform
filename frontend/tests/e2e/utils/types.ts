export type AuthCredentials = {
  email: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: {
    id: string;
    email: string;
    shop_id: string;
  };
};

export type Category = {
  id: string;
  name: string;
  shop_id: string;
  created_at: string;
};

export type Product = {
  id: string;
  category_id: string | null;
  name: string;
  sku: string;
  description: string | null;
  price: string;
  low_stock_threshold: number;
  is_active: boolean;
};

export type Paged<T> = {
  items: T[];
  total: number;
  skip: number;
  limit: number;
};

export type Notification = {
  id: string;
  event_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

export type Snapshot = {
  id: string;
  snapshot_type: string;
  payload: Record<string, unknown>;
  created_at: string;
};
