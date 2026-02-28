"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createSale, getProductStock, getProducts, getSales } from "@/lib/api";
import { formatMoney } from "@/lib/money";
import { useRequiredToken } from "@/components/use-required-token";
import { useCartStore } from "@/stores/cart-store";
import { usePreferencesStore } from "@/stores/preferences-store";

function toDateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export default function SalesPage() {
  const token = useRequiredToken();
  const currency = usePreferencesStore((s) => s.currency);
  const queryClient = useQueryClient();
  const today = toDateInputValue(new Date());
  const [page, setPage] = useState(1);
  const [fromDate, setFromDate] = useState(today);
  const [toDate, setToDate] = useState(today);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [stockByProduct, setStockByProduct] = useState<Record<string, number>>({});

  const cart = useCartStore((s) => s.items);
  const addItem = useCartStore((s) => s.addItem);
  const updateQty = useCartStore((s) => s.updateQty);
  const removeItem = useCartStore((s) => s.removeItem);
  const clearCart = useCartStore((s) => s.clear);

  const limit = 20;
  const skip = (page - 1) * limit;
  const invalidDateRange = Boolean(fromDate && toDate && fromDate > toDate);

  const salesQuery = useQuery({
    queryKey: ["sales", skip, limit, fromDate, toDate],
    queryFn: () => getSales(token as string, skip, limit, { fromDate, toDate }),
    enabled: Boolean(token) && !invalidDateRange
  });

  const productsQuery = useQuery({
    queryKey: ["products", 0, 20],
    queryFn: () => getProducts(token as string, 0, 20),
    enabled: Boolean(token)
  });

  const checkout = useMutation({
    mutationFn: async () =>
      createSale(token as string, {
        items: cart.map((line) => ({ product_id: line.productId, quantity: line.quantity }))
      }),
    onSuccess: async () => {
      clearCart();
      await queryClient.invalidateQueries({ queryKey: ["sales"] });
    }
  });

  const productOptions = productsQuery.data?.items ?? [];
  const hasPrev = page > 1;
  const hasNext = skip + limit < (salesQuery.data?.total ?? 0);
  const showPagination = (salesQuery.data?.total ?? 0) > limit;

  async function addToCartFromSelection() {
    if (!token || !selectedProductId) return;
    const product = productOptions.find((p) => p.id === selectedProductId);
    if (!product) return;
    addItem({ productId: product.id, name: product.name, unitPrice: Number(product.price) });
    const stock = await getProductStock(token, product.id);
    setStockByProduct((prev) => ({ ...prev, [product.id]: stock.current_stock }));
    setSelectedProductId("");
  }

  const cartTotal = useMemo(
    () => cart.reduce((sum, line) => sum + line.unitPrice * line.quantity, 0),
    [cart]
  );

  return (
    <main className="container col" data-testid="sales-page">
      <h1>Sales</h1>

      <section className="card col">
        <h2>Create Sale (POS)</h2>
        <div className="row">
          <select data-testid="sales-product-select" value={selectedProductId} onChange={(e) => setSelectedProductId(e.target.value)}>
            <option value="">Select product</option>
            {productOptions.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.sku})
              </option>
            ))}
          </select>
          <button className="btn" data-testid="sales-add-product" onClick={addToCartFromSelection} type="button">
            Add
          </button>
        </div>
        <table data-testid="sales-cart-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Qty</th>
              <th>Unit Price</th>
              <th>Advisory Stock</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {cart.map((line) => (
              <tr key={line.productId}>
                <td>{line.name}</td>
                <td>
                  <input
                    min={1}
                    type="number"
                    value={line.quantity}
                    onChange={(e) => updateQty(line.productId, Number(e.target.value))}
                    style={{ width: 70 }}
                  />
                </td>
                <td>{formatMoney(line.unitPrice, currency)}</td>
                <td>{stockByProduct[line.productId] ?? "-"}</td>
                <td>
                  <button className="btn secondary" onClick={() => removeItem(line.productId)} type="button">
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <strong>Total: {formatMoney(cartTotal, currency)}</strong>
          <button className="btn" data-testid="sales-checkout" disabled={checkout.isPending || cart.length === 0} onClick={() => checkout.mutate()}>
            {checkout.isPending ? "Processing..." : "Checkout"}
          </button>
        </div>
        {checkout.error && <div className="danger">{(checkout.error as Error).message}</div>}
      </section>

      <section className="card" data-testid="sales-history-section">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
          <h2>Sales History</h2>
          <div className="row" data-testid="sales-date-filter" style={{ gap: 10, alignItems: "flex-end", flexWrap: "wrap" }}>
            <label className="col" style={{ gap: 4 }}>
              <span>From</span>
              <input
                data-testid="sales-filter-from"
                type="date"
                value={fromDate}
                onChange={(e) => {
                  setFromDate(e.target.value);
                  setPage(1);
                }}
              />
            </label>
            <label className="col" style={{ gap: 4 }}>
              <span>To</span>
              <input
                data-testid="sales-filter-to"
                type="date"
                value={toDate}
                onChange={(e) => {
                  setToDate(e.target.value);
                  setPage(1);
                }}
              />
            </label>
            <button
              className="btn secondary"
              type="button"
              data-testid="sales-filter-reset"
              onClick={() => {
                setFromDate(today);
                setToDate(today);
                setPage(1);
              }}
            >
              Reset
            </button>
          </div>
        </div>
        {invalidDateRange && <div className="danger">From date cannot be after To date.</div>}
        {salesQuery.isLoading && <div>Loading sales...</div>}
        {salesQuery.error && <div className="danger">{(salesQuery.error as Error).message}</div>}
        <table data-testid="sales-history-table">
          <thead>
            <tr>
              <th>Sale Number</th>
              <th>Total</th>
              <th>Created</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {(salesQuery.data?.items ?? []).map((sale) => (
              <tr key={sale.id}>
                <td>{sale.sale_number}</td>
                <td>{formatMoney(sale.total_amount, currency)}</td>
                <td>{new Date(sale.created_at).toLocaleString()}</td>
                <td>
                  <Link href={`/sales/${sale.id}`}>View</Link>
                </td>
              </tr>
            ))}
            {(salesQuery.data?.items ?? []).length === 0 && !salesQuery.isLoading && !salesQuery.error && !invalidDateRange && (
              <tr>
                <td colSpan={4} className="muted">No sales found for selected date range.</td>
              </tr>
            )}
          </tbody>
        </table>
        {showPagination && (
          <div className="row" style={{ marginTop: 12 }} data-testid="sales-pagination">
            <button className="btn secondary" data-testid="sales-prev" disabled={!hasPrev || salesQuery.isLoading} onClick={() => setPage((x) => x - 1)}>
              Prev
            </button>
            <span className="muted" data-testid="sales-page-indicator">Page {page}</span>
            <button className="btn secondary" data-testid="sales-next" disabled={!hasNext || salesQuery.isLoading} onClick={() => setPage((x) => x + 1)}>
              Next
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
