"use client";

import { useMemo, useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";

import { getMonthlyComparison, getRevenueProfitSummary, getSnapshots } from "@/lib/api";
import { formatMoney } from "@/lib/money";
import { useRequiredToken } from "@/components/use-required-token";
import { usePreferencesStore } from "@/stores/preferences-store";

const PAGE_SIZE = 5;
const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function toDateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function startOfDay(dateValue: string): Date {
  return new Date(`${dateValue}T00:00:00`);
}

function endOfDay(dateValue: string): Date {
  return new Date(`${dateValue}T23:59:59.999`);
}

function formatPayloadValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (Array.isArray(value)) return `${value.length} item(s)`;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function formatMonthLabel(month: string): string {
  const [year, monthNum] = month.split("-");
  const idx = Number(monthNum) - 1;
  if (!year || Number.isNaN(idx) || idx < 0 || idx > 11) return month;
  return `${year}-${MONTHS_SHORT[idx]}`;
}

function monthDateRange(month: string): { fromDate: string; toDate: string } | null {
  const [yearText, monthText] = month.split("-");
  const year = Number(yearText);
  const monthIndex = Number(monthText) - 1;
  if (Number.isNaN(year) || Number.isNaN(monthIndex) || monthIndex < 0 || monthIndex > 11) return null;
  const from = new Date(Date.UTC(year, monthIndex, 1));
  const to = new Date(Date.UTC(year, monthIndex + 1, 0));
  const fromDate = from.toISOString().slice(0, 10);
  const toDate = to.toISOString().slice(0, 10);
  return { fromDate, toDate };
}

export default function AnalyticsPage() {
  const token = useRequiredToken();
  const currency = usePreferencesStore((s) => s.currency);
  const today = toDateInputValue(new Date());
  const [activeTab, setActiveTab] = useState<"insights" | "data-log">("insights");
  const [fromDate, setFromDate] = useState(today);
  const [toDate, setToDate] = useState(today);
  const [monthsWindow, setMonthsWindow] = useState(6);
  const [typePages, setTypePages] = useState<Record<string, number>>({});

  const monthlyComparisonQuery = useQuery({
    queryKey: ["insights-monthly-comparison", monthsWindow],
    queryFn: () => getMonthlyComparison(token as string, monthsWindow),
    enabled: Boolean(token)
  });

  const snapshotsQuery = useQuery({
    queryKey: ["analytics-snapshots"],
    queryFn: () => getSnapshots(token as string),
    enabled: Boolean(token)
  });

  const filteredSnapshots = useMemo(() => {
    const rows = snapshotsQuery.data ?? [];
    const from = fromDate ? startOfDay(fromDate) : null;
    const to = toDate ? endOfDay(toDate) : null;
    return rows.filter((snapshot) => {
      const createdAt = new Date(snapshot.created_at);
      if (Number.isNaN(createdAt.getTime())) return false;
      if (from && createdAt < from) return false;
      if (to && createdAt > to) return false;
      return true;
    });
  }, [snapshotsQuery.data, fromDate, toDate]);

  const groupedByType = useMemo(() => {
    const groups = new Map<string, typeof filteredSnapshots>();
    for (const snapshot of filteredSnapshots) {
      const key = snapshot.snapshot_type || "unknown";
      const current = groups.get(key) ?? [];
      current.push(snapshot);
      groups.set(key, current);
    }
    return Array.from(groups.entries()).map(([snapshotType, snapshots]) => ({
      snapshotType,
      snapshots: snapshots.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    }));
  }, [filteredSnapshots]);

  const monthlyComparison = monthlyComparisonQuery.data ?? [];
  const monthlyRevenueMax = Math.max(...monthlyComparison.map((row) => row.total_revenue), 1);
  const monthlyProfitQueries = useQueries({
    queries: monthlyComparison.map((row) => {
      const range = monthDateRange(row.month);
      return {
        queryKey: ["insights-monthly-profit", row.month],
        queryFn: () =>
          getRevenueProfitSummary(token as string, {
            fromDate: range?.fromDate ?? "",
            toDate: range?.toDate ?? ""
          }),
        enabled: Boolean(token && range)
      };
    })
  });
  const monthlyProfitByMonth = useMemo(() => {
    const map: Record<string, number | null> = {};
    monthlyComparison.forEach((row, idx) => {
      const profit = monthlyProfitQueries[idx]?.data?.total_profit;
      map[row.month] = typeof profit === "number" ? profit : null;
    });
    return map;
  }, [monthlyComparison, monthlyProfitQueries]);

  return (
    <main className="container col" data-testid="analytics-page">
      <h1>Insights</h1>

      <section className="col" style={{ gap: 0 }}>
        <section className="tabs" data-testid="insights-tabs">
          <div className="tabs-list" role="tablist" aria-label="Insights tabs">
            <button
              className={`tab-btn ${activeTab === "insights" ? "active" : ""}`}
              data-testid="insights-tab"
              role="tab"
              aria-selected={activeTab === "insights"}
              aria-controls="insights-panel"
              id="insights-tab-btn"
              onClick={() => setActiveTab("insights")}
              type="button"
            >
              Insights
            </button>
            <button
              className={`tab-btn ${activeTab === "data-log" ? "active" : ""}`}
              data-testid="data-log-tab"
              role="tab"
              aria-selected={activeTab === "data-log"}
              aria-controls="data-log-panel"
              id="data-log-tab-btn"
              onClick={() => setActiveTab("data-log")}
              type="button"
            >
              Data Log
            </button>
          </div>
        </section>

        {activeTab === "insights" && (
          <section className="tab-panel card col" data-testid="insights-monthly-card" role="tabpanel" id="insights-panel" aria-labelledby="insights-tab-btn">
            <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
              <strong>Monthly Comparison</strong>
              <select value={String(monthsWindow)} onChange={(e) => setMonthsWindow(Number(e.target.value))}>
                <option value="3">3 months</option>
                <option value="6">6 months</option>
                <option value="12">12 months</option>
              </select>
            </div>
            {monthlyComparisonQuery.isLoading && <div className="muted">Loading monthly comparison...</div>}
            {monthlyComparisonQuery.error && <div className="danger">Monthly comparison unavailable.</div>}
            {monthlyComparison.length === 0 && !monthlyComparisonQuery.isLoading && <div className="muted">No monthly sales data available.</div>}
            {monthlyComparison.length > 0 && (
              <div className="col" style={{ gap: 10 }} data-testid="insights-monthly-bars-chart">
                <svg width="100%" height="280" viewBox="0 0 680 280" role="img" aria-label="Monthly revenue chart">
                  <line x1="54" y1="24" x2="54" y2="220" stroke="#94a3b8" strokeWidth="1" />
                  <line x1="54" y1="220" x2="650" y2="220" stroke="#94a3b8" strokeWidth="1" />
                  <text x="14" y="22" fontSize="12" fontWeight="700" fill="#102133">Revenue</text>

                  {monthlyComparison.map((row, idx) => {
                    const slotWidth = 596 / monthlyComparison.length;
                    const barWidth = Math.min(44, slotWidth * 0.65);
                    const x = 54 + idx * slotWidth + (slotWidth - barWidth) / 2;
                    const barHeight = Math.max((row.total_revenue / monthlyRevenueMax) * 170, 6);
                    const y = 220 - barHeight;
                    return (
                      <g key={row.month}>
                        <rect x={x} y={y} width={barWidth} height={barHeight} rx="6" ry="6" fill="#f97316" />
                        <text x={x + barWidth / 2} y={y - 8} textAnchor="middle" fontSize="11" fontWeight="700" fill="#102133">
                          {formatMoney(row.total_revenue, currency)}
                        </text>
                        <text x={x + barWidth / 2} y="242" textAnchor="middle" fontSize="11" fontWeight="700" fill="#334155">
                          {formatMonthLabel(row.month)}
                        </text>
                        <text x={x + barWidth / 2} y="258" textAnchor="middle" fontSize="10" fontWeight="700" fill="#334155">
                          {monthlyProfitByMonth[row.month] === null ? "Profit: -" : `Profit: ${formatMoney(monthlyProfitByMonth[row.month] ?? 0, currency)}`}
                        </text>
                      </g>
                    );
                  })}
                </svg>

              </div>
            )}
          </section>
        )}

        {activeTab === "data-log" && (
          <div className="tab-panel card col" role="tabpanel" id="data-log-panel" aria-labelledby="data-log-tab-btn">
            {snapshotsQuery.isLoading && <div className="container">Loading analytics data log...</div>}
            {snapshotsQuery.error && <div className="container danger">{(snapshotsQuery.error as Error).message}</div>}

            {!snapshotsQuery.isLoading && !snapshotsQuery.error && (
              <>
                <div
                  className="row"
                  data-testid="analytics-date-filter"
                  style={{ gap: 16, alignItems: "flex-end", flexWrap: "wrap", marginBottom: 4 }}
                >
                  <label className="col" style={{ gap: 4 }}>
                    <span style={{ fontWeight: 700, color: "#102133" }}>From Date</span>
                    <input
                      data-testid="analytics-filter-from"
                      type="date"
                      value={fromDate}
                      onChange={(e) => {
                        setFromDate(e.target.value);
                        setTypePages({});
                      }}
                    />
                  </label>
                  <label className="col" style={{ gap: 4 }}>
                    <span style={{ fontWeight: 700, color: "#102133" }}>To Date</span>
                    <input
                      data-testid="analytics-filter-to"
                      type="date"
                      value={toDate}
                      onChange={(e) => {
                        setToDate(e.target.value);
                        setTypePages({});
                      }}
                    />
                  </label>
                </div>

                {groupedByType.length === 0 && (
                  <div className="muted" data-testid="analytics-empty-state">
                    No analytics data found for the selected date range.
                  </div>
                )}

                {groupedByType.map(({ snapshotType, snapshots }) => {
                  const currentPage = typePages[snapshotType] ?? 1;
                  const totalPages = Math.max(1, Math.ceil(snapshots.length / PAGE_SIZE));
                  const safePage = Math.min(currentPage, totalPages);
                  const showPagination = totalPages > 1;
                  const start = (safePage - 1) * PAGE_SIZE;
                  const pagedSnapshots = snapshots.slice(start, start + PAGE_SIZE);
                  const payloadKeys = Array.from(
                    new Set(
                      snapshots.flatMap((snapshot) =>
                        Object.keys(snapshot.payload ?? {}).filter((key) => key !== "event_type" && key !== "correlation_id")
                      )
                    )
                  );

                  return (
                    <section
                      key={snapshotType}
                      className="col"
                      data-testid="analytics-snapshot-card"
                      style={{ borderTop: "1px solid #e5edf6", paddingTop: 12 }}
                    >
                      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
                        <strong data-testid="analytics-event-type">{snapshotType}</strong>
                        <span className="muted">{snapshots.length} record(s)</span>
                      </div>

                      <div style={{ overflowX: "auto" }}>
                        <table data-testid={`analytics-table-${snapshotType}`}>
                          <thead>
                            <tr>
                              <th>Created At</th>
                              {payloadKeys.map((key) => (
                                <th key={key}>{key}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {pagedSnapshots.map((snapshot) => (
                              <tr key={snapshot.id}>
                                <td>{new Date(snapshot.created_at).toLocaleString()}</td>
                                {payloadKeys.map((key) => (
                                  <td key={`${snapshot.id}-${key}`}>{formatPayloadValue(snapshot.payload?.[key])}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {showPagination && (
                        <div className="row" style={{ alignItems: "center" }}>
                          <button
                            className="btn secondary"
                            disabled={safePage <= 1}
                            onClick={() => setTypePages((prev) => ({ ...prev, [snapshotType]: safePage - 1 }))}
                            type="button"
                          >
                            Prev
                          </button>
                          <span className="muted">
                            Page {safePage} of {totalPages}
                          </span>
                          <button
                            className="btn secondary"
                            disabled={safePage >= totalPages}
                            onClick={() => setTypePages((prev) => ({ ...prev, [snapshotType]: safePage + 1 }))}
                            type="button"
                          >
                            Next
                          </button>
                        </div>
                      )}
                    </section>
                  );
                })}
              </>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
