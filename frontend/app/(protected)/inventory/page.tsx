"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createBatch, getBatches, getProductsWithFilters, updateBatch } from "@/lib/api";
import { formatMoney } from "@/lib/money";
import { useRequiredToken } from "@/components/use-required-token";
import { usePreferencesStore } from "@/stores/preferences-store";

type BatchFormState = {
  productId: string;
  quantity: string;
  unitCost: string;
  expiryDate: string;
};

type BatchEditState = {
  batchId: string;
  unitCost: string;
  expiryDate: string;
};

function emptyForm(): BatchFormState {
  return {
    productId: "",
    quantity: "",
    unitCost: "",
    expiryDate: ""
  };
}

function validateBatchForm(form: BatchFormState) {
  if (!form.productId.trim()) return "Product is required.";
  if (!form.quantity.trim()) return "Quantity is required.";
  const quantity = Number(form.quantity);
  if (!Number.isInteger(quantity) || quantity <= 0) return "Quantity must be a whole number greater than 0.";
  if (!form.unitCost.trim()) return "Unit cost is required.";
  const unitCost = Number(form.unitCost);
  if (!Number.isFinite(unitCost) || unitCost < 0) return "Unit cost must be 0 or greater.";
  if (!form.expiryDate.trim()) return "Expiry date is required.";
  return null;
}

function validateBatchEditForm(form: BatchEditState) {
  if (!form.unitCost.trim()) return "Unit cost is required.";
  const unitCost = Number(form.unitCost);
  if (!Number.isFinite(unitCost) || unitCost <= 0) return "Unit cost must be greater than 0.";
  if (!form.expiryDate.trim()) return "Expiry date is required.";
  return null;
}

export default function InventoryPage() {
  const token = useRequiredToken();
  const currency = usePreferencesStore((s) => s.currency);
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [addingBatch, setAddingBatch] = useState(false);
  const [showInactiveProducts, setShowInactiveProducts] = useState(false);
  const [form, setForm] = useState<BatchFormState>(emptyForm);
  const [editForm, setEditForm] = useState<BatchEditState | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const limit = 20;
  const skip = (page - 1) * limit;

  const { data, isLoading, error } = useQuery({
    queryKey: ["batches", skip, limit],
    queryFn: () => getBatches(token as string, skip, limit),
    enabled: Boolean(token)
  });

  const activeProductsQuery = useQuery({
    queryKey: ["products", "inventory-batch-selector", "active"],
    queryFn: () => getProductsWithFilters(token as string, { skip: 0, limit: 100, isActive: true }),
    enabled: Boolean(token)
  });

  const inactiveProductsQuery = useQuery({
    queryKey: ["products", "inventory-batch-selector", "inactive"],
    queryFn: () => getProductsWithFilters(token as string, { skip: 0, limit: 100, isActive: false }),
    enabled: Boolean(token)
  });

  const createBatchMutation = useMutation({
    mutationFn: () =>
      createBatch(token as string, {
        product_id: form.productId,
        quantity: Number(form.quantity),
        unit_cost: Number(form.unitCost),
        expiry_date: form.expiryDate
      }),
    onSuccess: async () => {
      setAddingBatch(false);
      setForm(emptyForm());
      setMessage({ type: "success", text: "Batch created successfully." });
      await queryClient.invalidateQueries({ queryKey: ["batches"] });
    },
    onError: (err) => {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to create batch." });
    }
  });

  const updateBatchMutation = useMutation({
    mutationFn: (payload: { batchId: string; unit_cost?: number | null; expiry_date?: string | null }) =>
      updateBatch(token as string, payload.batchId, {
        unit_cost: payload.unit_cost,
        expiry_date: payload.expiry_date
      }),
    onSuccess: async () => {
      setEditForm(null);
      setMessage({ type: "success", text: "Batch updated successfully." });
      await queryClient.invalidateQueries({ queryKey: ["batches"] });
    },
    onError: (err) => {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to update batch." });
    }
  });

  const activeProducts = useMemo(() => activeProductsQuery.data?.items ?? [], [activeProductsQuery.data]);
  const inactiveProducts = useMemo(() => inactiveProductsQuery.data?.items ?? [], [inactiveProductsQuery.data]);
  const allProducts = useMemo(() => [...activeProducts, ...inactiveProducts], [activeProducts, inactiveProducts]);
  const productById = useMemo(
    () =>
      Object.fromEntries(allProducts.map((product) => [product.id, product])) as Record<
        string,
        (typeof allProducts)[number]
      >,
    [allProducts]
  );
  const productOptions = activeProducts;
  const visibleItems = useMemo(
    () =>
      (data?.items ?? []).filter((batch) => {
        if (showInactiveProducts) return true;
        return productById[batch.product_id]?.is_active !== false;
      }),
    [data?.items, productById, showInactiveProducts]
  );

  if (isLoading) return <div className="container">Loading inventory...</div>;
  if (error) return <div className="container danger">{(error as Error).message}</div>;
  if (!data) return null;
  const showPagination = data.total > limit;

  function onAddBatch() {
    setMessage(null);
    setEditForm(null);
    setAddingBatch(true);
    setForm(emptyForm());
  }

  function onSaveBatch() {
    const validation = validateBatchForm(form);
    if (validation) {
      setMessage({ type: "error", text: validation });
      return;
    }
    createBatchMutation.mutate();
  }

  function onStartEditBatch(batch: { id: string; unit_cost: string | null; expiry_date: string | null }) {
    setMessage(null);
    setAddingBatch(false);
    setForm(emptyForm());
    setEditForm({
      batchId: batch.id,
      unitCost: batch.unit_cost ?? "",
      expiryDate: batch.expiry_date ?? ""
    });
  }

  function onCancelEditBatch() {
    setEditForm(null);
    setMessage(null);
  }

  function onSaveEditBatch() {
    if (!editForm) return;
    const validation = validateBatchEditForm(editForm);
    if (validation) {
      setMessage({ type: "error", text: validation });
      return;
    }
    updateBatchMutation.mutate({
      batchId: editForm.batchId,
      unit_cost: editForm.unitCost.trim() ? Number(editForm.unitCost) : null,
      expiry_date: editForm.expiryDate.trim() ? editForm.expiryDate : null
    });
  }

  return (
    <main className="container col" data-testid="inventory-page">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1>Inventory</h1>
        <div className="row">
          <button className="btn secondary" data-testid="inventory-add-batch" disabled={addingBatch} onClick={onAddBatch} type="button">
            Add Batch
          </button>
          <Link className="btn" href="/inventory/movements/new">
            Stock Movement
          </Link>
        </div>
      </div>
      <label className="row" style={{ gap: 8, alignItems: "center", width: "fit-content" }}>
        <input
          checked={showInactiveProducts}
          data-testid="inventory-show-inactive-toggle"
          onChange={(e) => setShowInactiveProducts(e.target.checked)}
          type="checkbox"
        />
        Show inactive products/batches
      </label>

      {message && (
        <div className={message.type === "success" ? "success" : "danger"} data-testid="inventory-message">
          {message.text}
        </div>
      )}

      <div className="card">
        <table data-testid="inventory-table">
          <thead>
            <tr>
              <th>Batch ID</th>
              <th>Product ID</th>
              <th>Product</th>
              <th>Qty</th>
              <th>Unit Cost</th>
              <th>Expiry</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {addingBatch && (
              <tr data-testid="inventory-new-batch-row">
                <td>New</td>
                <td>-</td>
                <td>
                  <select
                    data-testid="inventory-batch-product"
                    value={form.productId}
                    onChange={(e) => setForm((prev) => ({ ...prev, productId: e.target.value }))}
                    style={{ maxWidth: 240, width: "100%" }}
                  >
                    <option value="">Select product</option>
                    {productOptions.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.sku})
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    data-testid="inventory-batch-quantity"
                    type="number"
                    min="1"
                    step="1"
                    value={form.quantity}
                    onChange={(e) => setForm((prev) => ({ ...prev, quantity: e.target.value }))}
                    style={{ width: 72 }}
                    required
                  />
                </td>
                <td>
                  <input
                    data-testid="inventory-batch-unit-cost"
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.unitCost}
                    onChange={(e) => setForm((prev) => ({ ...prev, unitCost: e.target.value }))}
                    style={{ width: 86 }}
                    required
                  />
                </td>
                <td>
                  <input
                    data-testid="inventory-batch-expiry"
                    type="date"
                    value={form.expiryDate}
                    onChange={(e) => setForm((prev) => ({ ...prev, expiryDate: e.target.value }))}
                    style={{ width: 140 }}
                    required
                  />
                </td>
                <td>
                  <div className="row" style={{ gap: 8, flexWrap: "nowrap", whiteSpace: "nowrap" }}>
                    <button
                      className="btn"
                      data-testid="inventory-batch-save"
                      disabled={createBatchMutation.isPending}
                      onClick={onSaveBatch}
                      style={{ padding: "6px 12px" }}
                      type="button"
                    >
                      Save
                    </button>
                    <button
                      className="btn secondary"
                      style={{ padding: "6px 12px" }}
                      onClick={() => {
                        setAddingBatch(false);
                        setForm(emptyForm());
                        setMessage(null);
                      }}
                      type="button"
                    >
                      Cancel
                    </button>
                  </div>
                </td>
              </tr>
            )}

            {visibleItems.map((b) => {
              const isEditing = editForm?.batchId === b.id;
              const currentEdit = isEditing ? editForm : null;
              const product = productById[b.product_id];
              const productLabel = product
                ? `${product.name} (${product.sku})${product.is_active ? "" : " [Inactive]"}`
                : b.product_id;
              return (
                <tr key={b.id} data-testid={`inventory-row-${b.id}`}>
                  <td>{b.id}</td>
                  <td>{b.product_id}</td>
                  <td>{productLabel}</td>
                  <td>{b.quantity}</td>
                  <td>
                    {currentEdit ? (
                      <input
                        data-testid="inventory-edit-unit-cost"
                        min="0"
                        step="0.01"
                        type="number"
                        value={currentEdit.unitCost}
                        onChange={(e) =>
                          setEditForm((prev) => (prev ? { ...prev, unitCost: e.target.value } : prev))
                        }
                        style={{ width: 100 }}
                      />
                    ) : (
                      b.unit_cost !== null ? formatMoney(b.unit_cost, currency) : "-"
                    )}
                  </td>
                  <td>
                    {currentEdit ? (
                      <input
                        data-testid="inventory-edit-expiry"
                        type="date"
                        value={currentEdit.expiryDate}
                        onChange={(e) =>
                          setEditForm((prev) => (prev ? { ...prev, expiryDate: e.target.value } : prev))
                        }
                      />
                    ) : (
                      b.expiry_date ?? "-"
                    )}
                  </td>
                  <td>
                    {currentEdit ? (
                      <div className="row" style={{ gap: 8, flexWrap: "nowrap", whiteSpace: "nowrap" }}>
                        <button
                          className="btn"
                          data-testid="inventory-edit-save"
                          disabled={updateBatchMutation.isPending}
                          onClick={onSaveEditBatch}
                          style={{ padding: "6px 12px" }}
                          type="button"
                        >
                          Save
                        </button>
                        <button
                          className="btn secondary"
                          data-testid="inventory-edit-cancel"
                          onClick={onCancelEditBatch}
                          style={{ padding: "6px 12px" }}
                          type="button"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        className="btn secondary"
                        data-testid="inventory-edit"
                        onClick={() => onStartEditBatch(b)}
                        type="button"
                      >
                        Edit
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {showPagination && (
        <div className="row">
          <button className="btn secondary" disabled={page <= 1} onClick={() => setPage((x) => x - 1)}>
            Prev
          </button>
          <span className="muted">Page {page}</span>
          <button className="btn secondary" disabled={skip + limit >= data.total} onClick={() => setPage((x) => x + 1)}>
            Next
          </button>
        </div>
      )}
    </main>
  );
}
