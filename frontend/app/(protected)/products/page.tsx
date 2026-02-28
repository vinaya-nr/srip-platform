"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createProduct,
  deleteProduct,
  getCategories,
  getProductsWithFilters,
  updateProduct
} from "@/lib/api";
import { formatMoney } from "@/lib/money";
import { useRequiredToken } from "@/components/use-required-token";
import { usePreferencesStore } from "@/stores/preferences-store";
import type { Product } from "@/lib/types";

type ProductFormState = {
  categoryId: string;
  name: string;
  sku: string;
  description: string;
  price: string;
  lowStockThreshold: string;
  isActive: boolean;
};

function toCreatePayload(form: ProductFormState) {
  return {
    category_id: form.categoryId.trim(),
    name: form.name.trim(),
    sku: form.sku.trim(),
    description: form.description.trim() || null,
    price: Number(form.price),
    low_stock_threshold: Number(form.lowStockThreshold || "1")
  };
}

function toUpdatePayload(form: ProductFormState) {
  return {
    category_id: form.categoryId.trim(),
    name: form.name.trim(),
    sku: form.sku.trim(),
    description: form.description.trim() || null,
    price: Number(form.price),
    low_stock_threshold: Number(form.lowStockThreshold || "1"),
    is_active: form.isActive
  };
}

function validateProduct(form: ProductFormState) {
  if (!form.name.trim()) return "Product name is required.";
  if (form.name.trim().length > 180) return "Product name must be at most 180 characters.";
  if (!form.sku.trim()) return "SKU is required.";
  if (form.sku.trim().length > 80) return "SKU must be at most 80 characters.";
  if (!form.categoryId.trim()) return "Category is required.";
  const price = Number(form.price);
  if (!Number.isFinite(price) || price <= 0) return "Price must be greater than 0.";
  const threshold = Number(form.lowStockThreshold || "1");
  if (!Number.isInteger(threshold) || threshold < 1) return "Low stock threshold must be 1 or greater.";
  return null;
}

function productToForm(p: Product): ProductFormState {
  return {
    categoryId: p.category_id ?? "",
    name: p.name,
    sku: p.sku,
    description: p.description ?? "",
    price: p.price,
    lowStockThreshold: String(p.low_stock_threshold),
    isActive: p.is_active
  };
}

function emptyProductForm(): ProductFormState {
  return {
    categoryId: "",
    name: "",
    sku: "",
    description: "",
    price: "",
    lowStockThreshold: "1",
    isActive: true
  };
}

export default function ProductsPage() {
  const token = useRequiredToken();
  const currency = usePreferencesStore((s) => s.currency);
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [searchApplied, setSearchApplied] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const [adding, setAdding] = useState(false);
  const [newForm, setNewForm] = useState<ProductFormState>(emptyProductForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<ProductFormState>(emptyProductForm);
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const limit = 20;
  const skip = (page - 1) * limit;

  const productsQuery = useQuery({
    queryKey: ["products", skip, limit, searchApplied, categoryFilter],
    queryFn: () =>
      getProductsWithFilters(token as string, {
        skip,
        limit,
        search: searchApplied || undefined,
        categoryId: categoryFilter || undefined
      }),
    enabled: Boolean(token)
  });

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: () => getCategories(token as string),
    enabled: Boolean(token)
  });

  const createMutation = useMutation({
    mutationFn: (payload: ProductFormState) => createProduct(token as string, toCreatePayload(payload)),
    onSuccess: async () => {
      setAdding(false);
      setNewForm(emptyProductForm());
      setMessage({ type: "success", text: "Product created successfully." });
      await queryClient.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (err) => {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to create product." });
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, form }: { id: string; form: ProductFormState }) =>
      updateProduct(token as string, id, toUpdatePayload(form)),
    onSuccess: async () => {
      setEditingId(null);
      setEditForm(emptyProductForm());
      setMessage({ type: "success", text: "Product updated successfully." });
      await queryClient.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (err) => {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to update product." });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (productId: string) => deleteProduct(token as string, productId),
    onSuccess: async () => {
      setDeleteTarget(null);
      setMessage({ type: "success", text: "Product deleted successfully." });
      await queryClient.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (err) => {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to delete product." });
    }
  });

  const products = useMemo(() => productsQuery.data?.items ?? [], [productsQuery.data]);
  const categories = categoriesQuery.data ?? [];

  if (productsQuery.isLoading) return <div className="container">Loading products...</div>;
  if (productsQuery.error) return <div className="container danger">{(productsQuery.error as Error).message}</div>;
  if (!productsQuery.data) return null;

  const hasPrev = page > 1;
  const hasNext = skip + limit < productsQuery.data.total;
  const showPagination = productsQuery.data.total > limit;

  function handleSearchSubmit() {
    setPage(1);
    setSearchApplied(searchInput.trim());
  }

  function handleCategoryFilterChange(value: string) {
    setPage(1);
    setCategoryFilter(value);
  }

  function saveNewProduct() {
    const validation = validateProduct(newForm);
    if (validation) {
      setMessage({ type: "error", text: validation });
      return;
    }
    createMutation.mutate(newForm);
  }

  function startEdit(product: Product) {
    setMessage(null);
    setEditingId(product.id);
    setEditForm(productToForm(product));
  }

  function saveEdit() {
    if (!editingId) return;
    const validation = validateProduct(editForm);
    if (validation) {
      setMessage({ type: "error", text: validation });
      return;
    }
    updateMutation.mutate({ id: editingId, form: editForm });
  }

  return (
    <main className="container col" data-testid="products-page">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1>Products</h1>
        <button className="btn" data-testid="products-add" disabled={adding} onClick={() => setAdding(true)} type="button">
          Add Product
        </button>
      </div>

      <div className="card">
        <div className="row" style={{ alignItems: "center", flexWrap: "wrap" }}>
          <input
            data-testid="products-search-input"
            placeholder="Search by name or SKU"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            style={{ minWidth: 260 }}
          />
          <button className="btn secondary" data-testid="products-search-button" onClick={handleSearchSubmit} type="button">
            Search
          </button>
          <select
            data-testid="products-category-filter"
            value={categoryFilter}
            onChange={(e) => handleCategoryFilterChange(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <button
            className="btn secondary"
            type="button"
            onClick={() => {
              setSearchInput("");
              setSearchApplied("");
              setCategoryFilter("");
              setPage(1);
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {message && (
        <div className={message.type === "success" ? "success" : "danger"} data-testid="products-message">
          {message.text}
        </div>
      )}

      <div className="card">
        <table data-testid="products-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>SKU</th>
              <th>Category</th>
              <th>Price</th>
              <th>Threshold</th>
              <th>Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {adding && (
              <tr data-testid="products-new-row">
                <td>
                  <input value={newForm.name} onChange={(e) => setNewForm((prev) => ({ ...prev, name: e.target.value }))} />
                </td>
                <td>
                  <input value={newForm.sku} onChange={(e) => setNewForm((prev) => ({ ...prev, sku: e.target.value }))} />
                </td>
                <td>
                  <select
                    value={newForm.categoryId}
                    onChange={(e) => setNewForm((prev) => ({ ...prev, categoryId: e.target.value }))}
                  >
                    <option value="" disabled>
                      Select category
                    </option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={newForm.price}
                    onChange={(e) => setNewForm((prev) => ({ ...prev, price: e.target.value }))}
                    style={{ width: 90 }}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={newForm.lowStockThreshold}
                    onChange={(e) => setNewForm((prev) => ({ ...prev, lowStockThreshold: e.target.value }))}
                    style={{ width: 90 }}
                  />
                </td>
                <td>Yes</td>
                <td>
                  <div className="row">
                    <button className="btn" disabled={createMutation.isPending} onClick={saveNewProduct} type="button">
                      Save
                    </button>
                    <button
                      className="btn secondary"
                      onClick={() => {
                        setAdding(false);
                        setNewForm(emptyProductForm());
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

            {products.map((p) => {
              const isEditing = editingId === p.id;
              const categoryName = categories.find((c) => c.id === p.category_id)?.name ?? "-";
              return (
                <tr key={p.id}>
                  <td>
                    {isEditing ? (
                      <input value={editForm.name} onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))} />
                    ) : (
                      p.name
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input value={editForm.sku} onChange={(e) => setEditForm((prev) => ({ ...prev, sku: e.target.value }))} />
                    ) : (
                      p.sku
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <select value={editForm.categoryId} onChange={(e) => setEditForm((prev) => ({ ...prev, categoryId: e.target.value }))}>
                        <option value="" disabled>
                          Select category
                        </option>
                        {categories.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      categoryName
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        step="0.01"
                        min="0.01"
                        value={editForm.price}
                        onChange={(e) => setEditForm((prev) => ({ ...prev, price: e.target.value }))}
                        style={{ width: 90 }}
                      />
                    ) : (
                      formatMoney(p.price, currency)
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={editForm.lowStockThreshold}
                        onChange={(e) => setEditForm((prev) => ({ ...prev, lowStockThreshold: e.target.value }))}
                        style={{ width: 90 }}
                      />
                    ) : (
                      p.low_stock_threshold
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <select
                        value={editForm.isActive ? "true" : "false"}
                        onChange={(e) => setEditForm((prev) => ({ ...prev, isActive: e.target.value === "true" }))}
                      >
                        <option value="true">Yes</option>
                        <option value="false">No</option>
                      </select>
                    ) : p.is_active ? (
                      "Yes"
                    ) : (
                      "No"
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <div className="row">
                        <button className="btn" disabled={updateMutation.isPending} onClick={saveEdit} type="button">
                          Save
                        </button>
                        <button
                          className="btn secondary"
                          onClick={() => {
                            setEditingId(null);
                            setEditForm(emptyProductForm());
                            setMessage(null);
                          }}
                          type="button"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="row">
                        <button className="btn secondary" onClick={() => startEdit(p)} type="button">
                          Edit
                        </button>
                        <button className="btn danger-btn" onClick={() => setDeleteTarget(p)} type="button">
                          Delete
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {showPagination && (
        <div className="row" data-testid="products-pagination">
          <button className="btn secondary" data-testid="products-prev" disabled={!hasPrev} onClick={() => setPage((x) => x - 1)}>
            Prev
          </button>
          <span className="muted" data-testid="products-page-indicator">
            Page {page}
          </span>
          <button className="btn secondary" data-testid="products-next" disabled={!hasNext} onClick={() => setPage((x) => x + 1)}>
            Next
          </button>
        </div>
      )}

      {deleteTarget && (
        <div className="modal-overlay" data-testid="products-delete-modal">
          <div className="modal-card col">
            <h3>Confirm Delete</h3>
            <p>
              Delete product <strong>{deleteTarget.name}</strong>?
            </p>
            <div className="row" style={{ justifyContent: "flex-end" }}>
              <button className="btn secondary" onClick={() => setDeleteTarget(null)} type="button">
                No
              </button>
              <button
                className="btn danger-btn"
                data-testid="products-confirm-delete"
                disabled={deleteMutation.isPending}
                onClick={() => deleteMutation.mutate(deleteTarget.id)}
                type="button"
              >
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
