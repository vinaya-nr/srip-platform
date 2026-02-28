"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getDashboardSummary, getRevenueProfitSummary, getTopProducts } from "@/lib/api";
import { formatMoney } from "@/lib/money";
import { useRequiredToken } from "@/components/use-required-token";
import { usePreferencesStore } from "@/stores/preferences-store";

function toDateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function polarToCartesian(cx: number, cy: number, radius: number, angleDeg: number) {
  const angleRad = (Math.PI / 180) * angleDeg;
  return {
    x: cx + radius * Math.cos(angleRad),
    y: cy + radius * Math.sin(angleRad)
  };
}

function describePieSlice(cx: number, cy: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, radius, startAngle);
  const end = polarToCartesian(cx, cy, radius, endAngle);
  const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x} ${end.y} Z`;
}

export default function DashboardPage() {
  const token = useRequiredToken();
  const currency = usePreferencesStore((s) => s.currency);
  const today = toDateInputValue(new Date());
  const [fromDate, setFromDate] = useState(today);
  const [toDate, setToDate] = useState(today);
  const [trendFromDate, setTrendFromDate] = useState(today);
  const [trendToDate, setTrendToDate] = useState(today);

  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => getDashboardSummary(token as string),
    enabled: Boolean(token),
    staleTime: 60_000
  });

  const topProductsQuery = useQuery({
    queryKey: ["dashboard-top-products", fromDate, toDate],
    queryFn: () => getTopProducts(token as string, { fromDate, toDate, limit: 5 }),
    enabled: Boolean(token) && fromDate <= toDate
  });

  const revenueSeriesQuery = useQuery({
    queryKey: ["dashboard-revenue-profit", trendFromDate, trendToDate],
    queryFn: () => getRevenueProfitSummary(token as string, { fromDate: trendFromDate, toDate: trendToDate }),
    enabled: Boolean(token)
  });

  if (isLoading) return <div className="container">Loading dashboard...</div>;
  if (error) return <div className="container danger">{(error as Error).message}</div>;
  if (!data) return null;

  const topProducts = topProductsQuery.data ?? [];
  const topProductMaxQty = Math.max(...topProducts.map((row) => row.total_quantity), 1);
  const topProductsTickStep = Math.max(1, Math.ceil(topProductMaxQty / 5));
  const topProductsYAxisMax = topProductsTickStep * 5;
  const revenueValue = Math.max(0, revenueSeriesQuery.data?.total_revenue ?? 0);
  const profitValue = Math.max(0, revenueSeriesQuery.data?.total_profit ?? 0);
  const pieTotal = Math.max(revenueValue + profitValue, 1);

  return (
    <main className="container col" data-testid="dashboard-page">
      <h1 data-testid="dashboard-title">Dashboard</h1>
      <section className="grid grid-4">
        <div className="card" data-testid="summary-today-sales"><strong>Today Sales</strong><div>{data.today_sales_total}</div></div>
        <div className="card" data-testid="summary-today-revenue"><strong>Today Revenue</strong><div>{formatMoney(data.today_revenue_total, currency)}</div></div>
        <div className="card" data-testid="summary-active-products"><strong>Active Products</strong><div>{data.active_products_count}</div></div>
        <Link href="/notifications" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card" data-testid="summary-low-stock">
            <strong>Low Stock</strong>
            <div>{data.low_stock_count}</div>
            {data.low_stock_count >= 1 && (
              <div className="muted" style={{ marginTop: 6 }}>
                View details in notifications
              </div>
            )}
          </div>
        </Link>
      </section>
      <section className="card" data-testid="summary-unread-notifications">
        <strong>Unread Notifications</strong>
        <div>{data.unread_notifications_count}</div>
      </section>

      <section className="grid grid-2">
        <article className="card col" data-testid="dashboard-top-products-card">
          <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
            <strong>Top 5 Products Sold</strong>
            <span className="muted">
              {fromDate} to {toDate}
            </span>
          </div>
          <div className="row" style={{ gap: 8, alignItems: "flex-end", flexWrap: "wrap" }}>
            <label className="col" style={{ gap: 4 }}>
              <span className="muted">From</span>
              <input
                data-testid="dashboard-top-from"
                type="date"
                value={fromDate}
                onChange={(e) => {
                  const nextFrom = e.target.value;
                  setFromDate(nextFrom);
                  if (toDate < nextFrom) setToDate(nextFrom);
                }}
              />
            </label>
            <label className="col" style={{ gap: 4 }}>
              <span className="muted">To</span>
              <input
                data-testid="dashboard-top-to"
                type="date"
                value={toDate}
                onChange={(e) => {
                  const nextTo = e.target.value;
                  setToDate(nextTo);
                  if (nextTo < fromDate) setFromDate(nextTo);
                }}
              />
            </label>
          </div>
          {fromDate > toDate && <div className="danger">From date cannot be greater than To date.</div>}
          {topProductsQuery.isLoading && <div className="muted">Loading top products...</div>}
          {topProductsQuery.error && (
            <div className="danger">
              {topProductsQuery.error instanceof Error ? topProductsQuery.error.message : "Top products unavailable."}
            </div>
          )}
          {topProducts.length === 0 && !topProductsQuery.isLoading && !topProductsQuery.error && (
            <div className="muted">No sales in selected range.</div>
          )}
          {topProducts.length > 0 && (
            <div style={{ overflowX: "auto" }}>
              <svg
                data-testid="dashboard-top-products-chart"
                viewBox="0 0 560 260"
                width="100%"
                height={260}
                role="img"
                aria-label="Top products sold bar chart"
              >
                <rect x="0" y="0" width="560" height="260" fill="#ffffff" />
                <g transform="translate(56,20)">
                  {Array.from({ length: 5 }).map((_, index) => {
                    const value = topProductsTickStep * (index + 1);
                    const y = 190 - (190 * value) / topProductsYAxisMax;
                    return (
                      <g key={`top-products-grid-${index}`}>
                        <line x1="0" y1={y} x2="476" y2={y} stroke="#e2e8f0" strokeWidth="1" />
                        <text x="-10" y={y + 5} textAnchor="end" fontSize="13" fontWeight="700" fill="#1e293b">
                          {value}
                        </text>
                      </g>
                    );
                  })}

                  <line x1="0" y1="190" x2="476" y2="190" stroke="#334155" strokeWidth="1.2" />
                  <line x1="0" y1="0" x2="0" y2="190" stroke="#334155" strokeWidth="1.2" />

                  {topProducts.map((row, idx) => {
                    const slotWidth = 476 / topProducts.length;
                    const barWidth = Math.min(48, slotWidth * 0.6);
                    const barHeight = Math.max((row.total_quantity / topProductsYAxisMax) * 190, 2);
                    const x = idx * slotWidth + (slotWidth - barWidth) / 2;
                    const y = 190 - barHeight;
                    const label = row.product_name.length > 12 ? `${row.product_name.slice(0, 12)}...` : row.product_name;
                    return (
                      <g key={row.product_id}>
                        <rect
                          x={x}
                          y={y}
                          width={barWidth}
                          height={barHeight}
                          rx="4"
                          fill="#ec4899"
                        >
                          <title>{`${row.product_name}: ${row.total_quantity} sold (${formatMoney(row.total_revenue, currency)})`}</title>
                        </rect>
                        <text
                          x={x + barWidth / 2}
                          y={y - 6}
                          textAnchor="middle"
                          fontSize="13"
                          fontWeight="700"
                          fill="#1e293b"
                        >
                          {row.total_quantity}
                        </text>
                        <text
                          x={x + barWidth / 2}
                          y="210"
                          textAnchor="middle"
                          fontSize="13"
                          fontWeight="700"
                          fill="#1e293b"
                        >
                          {label}
                        </text>
                      </g>
                    );
                  })}
                </g>
              </svg>
            </div>
          )}
        </article>

        <article className="card col" data-testid="dashboard-revenue-trend-card">
          <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
            <strong>Revenue vs Profit</strong>
            <span className="muted">
              {trendFromDate} to {trendToDate}
            </span>
          </div>
          <div className="row" style={{ gap: 8, alignItems: "flex-end", flexWrap: "wrap" }}>
            <label className="col" style={{ gap: 4 }}>
              <span className="muted">From</span>
              <input type="date" value={trendFromDate} onChange={(e) => setTrendFromDate(e.target.value)} />
            </label>
            <label className="col" style={{ gap: 4 }}>
              <span className="muted">To</span>
              <input type="date" value={trendToDate} onChange={(e) => setTrendToDate(e.target.value)} />
            </label>
          </div>
          {revenueSeriesQuery.isLoading && <div className="muted">Loading revenue and profit...</div>}
          {revenueSeriesQuery.error && <div className="danger">Revenue/profit chart unavailable.</div>}
          {!revenueSeriesQuery.error && !revenueSeriesQuery.isLoading && revenueValue === 0 && profitValue === 0 && (
            <div className="muted">No revenue data for this range.</div>
          )}
          {!revenueSeriesQuery.error && !revenueSeriesQuery.isLoading && (revenueValue > 0 || profitValue > 0) && (
            <div className="row" style={{ alignItems: "center", justifyContent: "space-between", flexWrap: "wrap" }}>
              <svg width="260" height="220" viewBox="0 0 260 220" role="img" aria-label="Revenue and profit pie chart">
                {(() => {
                  const cx = 100;
                  const cy = 110;
                  const radius = 78;
                  const outline = "#475569";
                  const revenueColor = "#3b82f6";
                  const profitColor = "#14b8a6";
                  const revenueAngle = (revenueValue / pieTotal) * 360;
                  const profitAngle = (profitValue / pieTotal) * 360;
                  const startAngle = -90;
                  const revenueEnd = startAngle + revenueAngle;
                  const profitEnd = revenueEnd + profitAngle;
                  const revenueMid = startAngle + revenueAngle / 2;
                  const profitMid = revenueEnd + profitAngle / 2;
                  const revenueLabel = polarToCartesian(cx, cy, radius * 0.55, revenueMid);
                  const profitLabel = polarToCartesian(cx, cy, radius * 0.55, profitMid);
                  return (
                    <g>
                      <path
                        d={describePieSlice(cx, cy, radius, startAngle, revenueEnd)}
                        fill={revenueColor}
                        stroke={outline}
                        strokeWidth="1.2"
                      />
                      <path
                        d={describePieSlice(cx, cy, radius, revenueEnd, profitEnd)}
                        fill={profitColor}
                        stroke={outline}
                        strokeWidth="1.2"
                      />
                      <circle cx={cx} cy={cy} r="16" fill="none" stroke={outline} strokeWidth="1.2" />

                      <text x={revenueLabel.x} y={revenueLabel.y} textAnchor="middle" fontSize="10" fontWeight="700" fill="#ffffff">
                        {formatMoney(revenueValue, currency)}
                      </text>
                      <text x={profitLabel.x} y={profitLabel.y} textAnchor="middle" fontSize="10" fontWeight="700" fill="#ffffff">
                        {formatMoney(profitValue, currency)}
                      </text>
                    </g>
                  );
                })()}
              </svg>

              <div className="col" style={{ minWidth: 180 }}>
                <div className="row" style={{ alignItems: "center", gap: 8 }}>
                  <span style={{ width: 12, height: 12, borderRadius: 99, background: "#3b82f6", display: "inline-block" }} />
                  <strong>Revenue</strong>
                </div>
                <span className="muted">{formatMoney(revenueValue, currency)}</span>
                <div className="row" style={{ alignItems: "center", gap: 8, marginTop: 10 }}>
                  <span style={{ width: 12, height: 12, borderRadius: 99, background: "#14b8a6", display: "inline-block" }} />
                  <strong>Profit</strong>
                </div>
                <span className="muted">{formatMoney(profitValue, currency)}</span>
              </div>
            </div>
          )}
        </article>

      </section>
    </main>
  );
}
