"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { getSale } from "@/lib/api";
import { formatMoney } from "@/lib/money";
import { useRequiredToken } from "@/components/use-required-token";
import { usePreferencesStore } from "@/stores/preferences-store";

export default function SaleDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const token = useRequiredToken();
  const currency = usePreferencesStore((s) => s.currency);
  const saleId = params.id;

  const { data, isLoading, error } = useQuery({
    queryKey: ["sale", saleId],
    queryFn: () => getSale(token as string, saleId),
    enabled: Boolean(token && saleId)
  });

  if (isLoading) return <div className="container">Loading sale...</div>;
  if (error) return <div className="container danger">{(error as Error).message}</div>;
  if (!data) return null;

  return (
    <main className="container col" data-testid="sale-detail-page">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1 data-testid="sale-detail-title">Sale {data.sale_number}</h1>
        <button
          className="btn secondary"
          data-testid="sale-detail-back"
          onClick={() => {
            if (window.history.length > 1) {
              router.back();
            } else {
              router.push("/sales");
            }
          }}
          type="button"
        >
          Back
        </button>
      </div>

      <div className="card col" data-testid="sale-detail-summary">
        <div data-testid="sale-detail-id">Sale ID: {data.id}</div>
        <div data-testid="sale-detail-total">Total: {formatMoney(data.total_amount, currency)}</div>
        <div data-testid="sale-detail-created">Created: {new Date(data.created_at).toLocaleString()}</div>
      </div>
      <div className="card">
        <div style={{ maxHeight: 360, overflowY: "auto", overflowX: "auto" }} data-testid="sale-detail-items-scroll">
          <table data-testid="sale-detail-items">
            <thead>
              <tr>
                <th>Product</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => (
                <tr key={`${item.product_id}-${item.quantity}-${item.line_total}`}>
                  <td>{item.product_name ?? item.product_id}</td>
                  <td>{item.quantity}</td>
                  <td>{formatMoney(item.unit_price, currency)}</td>
                  <td>{formatMoney(item.line_total, currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
