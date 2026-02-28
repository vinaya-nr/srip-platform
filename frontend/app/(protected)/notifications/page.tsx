"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getNotifications, markNotificationRead } from "@/lib/api";
import { useRequiredToken } from "@/components/use-required-token";

function toDateInputValue(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function NotificationsPage() {
  const token = useRequiredToken();
  const queryClient = useQueryClient();
  const today = toDateInputValue(new Date());
  const [page, setPage] = useState(1);
  const [fromDate, setFromDate] = useState(today);
  const [toDate, setToDate] = useState(today);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const limit = 20;
  const skip = (page - 1) * limit;
  const invalidDateRange = fromDate > toDate;

  const { data, isLoading, error } = useQuery({
    queryKey: ["notifications", skip, limit, fromDate, toDate],
    queryFn: () =>
      getNotifications(token as string, skip, limit, {
        fromDate,
        toDate
      }),
    enabled: Boolean(token) && !invalidDateRange
  });

  const markReadMutation = useMutation({
    mutationFn: (notificationId: string) => markNotificationRead(token as string, notificationId),
    onSuccess: async () => {
      setMessage({ type: "success", text: "Notification marked as read." });
      await queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
    onError: (err) => {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to mark notification as read." });
    }
  });

  if (isLoading && !invalidDateRange) return <div className="container">Loading notifications...</div>;
  if (error && !invalidDateRange) return <div className="container danger">{(error as Error).message}</div>;
  const notifications = data?.items ?? [];
  const total = data?.total ?? 0;
  const showPagination = total > limit;

  return (
    <main className="container col" data-testid="notifications-page">
      <h1>Notifications</h1>
      <div className="row" style={{ alignItems: "end", gap: 12 }}>
        <div className="col" style={{ minWidth: 180 }}>
          <label htmlFor="notifications-from-date">From</label>
          <input
            id="notifications-from-date"
            data-testid="notifications-from-date"
            type="date"
            value={fromDate}
            onChange={(e) => {
              setFromDate(e.target.value);
              setPage(1);
              setMessage(null);
            }}
          />
        </div>
        <div className="col" style={{ minWidth: 180 }}>
          <label htmlFor="notifications-to-date">To</label>
          <input
            id="notifications-to-date"
            data-testid="notifications-to-date"
            type="date"
            value={toDate}
            onChange={(e) => {
              setToDate(e.target.value);
              setPage(1);
              setMessage(null);
            }}
          />
        </div>
      </div>
      {message && (
        <div className={message.type === "success" ? "success" : "danger"} data-testid="notifications-message">
          {message.text}
        </div>
      )}
      {invalidDateRange && <div className="danger">From date cannot be after To date.</div>}
      <div className="card">
        <table data-testid="notifications-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Message</th>
              <th>Type</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {notifications.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted">
                  No notifications in selected date range.
                </td>
              </tr>
            ) : (
              notifications.map((n) => (
                <tr key={n.id}>
                  <td>{n.title}</td>
                  <td>{n.message}</td>
                  <td>{n.event_type}</td>
                  <td>{n.is_read ? "Read" : "Unread"}</td>
                  <td>{new Date(n.created_at).toLocaleString()}</td>
                  <td>
                    {n.is_read ? (
                      "-"
                    ) : (
                      <button
                        className="btn secondary"
                        data-testid={`notifications-mark-read-${n.id}`}
                        disabled={markReadMutation.isPending}
                        onClick={() => markReadMutation.mutate(n.id)}
                        type="button"
                      >
                        Mark Read
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {showPagination && (
        <div className="row">
          <button className="btn secondary" disabled={page <= 1} onClick={() => setPage((x) => x - 1)}>
            Prev
          </button>
          <span className="muted">Page {page}</span>
          <button className="btn secondary" disabled={skip + limit >= total} onClick={() => setPage((x) => x + 1)}>
            Next
          </button>
        </div>
      )}
    </main>
  );
}
