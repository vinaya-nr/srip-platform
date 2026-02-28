"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createCategory, deleteCategory, getCategories, updateCategory } from "@/lib/api";
import { useRequiredToken } from "@/components/use-required-token";
import type { Category } from "@/lib/types";

function validateCategoryName(value: string) {
  const name = value.trim();
  if (!name) return "Category name is required.";
  if (name.length > 120) return "Category name must be at most 120 characters.";
  return null;
}

export default function CategoriesPage() {
  const token = useRequiredToken();
  const queryClient = useQueryClient();

  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["categories"],
    queryFn: () => getCategories(token as string),
    enabled: Boolean(token)
  });

  const createMutation = useMutation({
    mutationFn: (payload: { name: string }) => createCategory(token as string, payload),
    onSuccess: async () => {
      setAdding(false);
      setNewName("");
      setMessage({ type: "success", text: "Category created successfully." });
      await queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
    onError: (err) => {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to create category." });
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => updateCategory(token as string, id, { name }),
    onSuccess: async () => {
      setEditingId(null);
      setEditName("");
      setMessage({ type: "success", text: "Category updated successfully." });
      await queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
    onError: (err) => {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to update category." });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (categoryId: string) => deleteCategory(token as string, categoryId),
    onSuccess: async () => {
      setDeleteTarget(null);
      setMessage({ type: "success", text: "Category deleted successfully." });
      await queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
    onError: (err) => {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to delete category." });
    }
  });

  const rows = useMemo(() => data ?? [], [data]);

  if (isLoading) return <div className="container">Loading categories...</div>;
  if (error) return <div className="container danger">{(error as Error).message}</div>;

  function onAddClick() {
    setMessage(null);
    setAdding(true);
    setNewName("");
  }

  function onSaveNew() {
    const validation = validateCategoryName(newName);
    if (validation) {
      setMessage({ type: "error", text: validation });
      return;
    }
    createMutation.mutate({ name: newName.trim() });
  }

  function onEditClick(category: Category) {
    setMessage(null);
    setEditingId(category.id);
    setEditName(category.name);
  }

  function onSaveEdit() {
    if (!editingId) return;
    const validation = validateCategoryName(editName);
    if (validation) {
      setMessage({ type: "error", text: validation });
      return;
    }
    updateMutation.mutate({ id: editingId, name: editName.trim() });
  }

  return (
    <main className="container col" data-testid="categories-page">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1>Categories</h1>
        <button className="btn" data-testid="categories-add" disabled={adding} onClick={onAddClick} type="button">
          Add Category
        </button>
      </div>

      {message && (
        <div className={message.type === "success" ? "success" : "danger"} data-testid="categories-message">
          {message.text}
        </div>
      )}

      <div className="card">
        <table data-testid="categories-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {adding && (
              <tr data-testid="categories-new-row">
                <td>
                  <input
                    data-testid="categories-new-name"
                    placeholder="Category name"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                  />
                </td>
                <td>-</td>
                <td>
                  <div className="row">
                    <button
                      className="btn"
                      data-testid="categories-save-new"
                      disabled={createMutation.isPending}
                      onClick={onSaveNew}
                      type="button"
                    >
                      Save
                    </button>
                    <button
                      className="btn secondary"
                      onClick={() => {
                        setAdding(false);
                        setNewName("");
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

            {rows.map((c) => {
              const isEditing = editingId === c.id;
              return (
                <tr key={c.id}>
                  <td>
                    {isEditing ? (
                      <input value={editName} onChange={(e) => setEditName(e.target.value)} data-testid={`categories-edit-name-${c.id}`} />
                    ) : (
                      c.name
                    )}
                  </td>
                  <td>{new Date(c.created_at).toLocaleString()}</td>
                  <td>
                    {isEditing ? (
                      <div className="row">
                        <button
                          className="btn"
                          data-testid={`categories-save-${c.id}`}
                          disabled={updateMutation.isPending}
                          onClick={onSaveEdit}
                          type="button"
                        >
                          Save
                        </button>
                        <button
                          className="btn secondary"
                          onClick={() => {
                            setEditingId(null);
                            setEditName("");
                            setMessage(null);
                          }}
                          type="button"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="row">
                        <button className="btn secondary" data-testid={`categories-edit-${c.id}`} onClick={() => onEditClick(c)} type="button">
                          Edit
                        </button>
                        <button
                          className="btn danger-btn"
                          data-testid={`categories-delete-${c.id}`}
                          onClick={() => setDeleteTarget(c)}
                          type="button"
                        >
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

      {deleteTarget && (
        <div className="modal-overlay" data-testid="categories-delete-modal">
          <div className="modal-card col">
            <h3>Confirm Delete</h3>
            <p>
              Delete category <strong>{deleteTarget.name}</strong>?
            </p>
            <div className="row" style={{ justifyContent: "flex-end" }}>
              <button className="btn secondary" onClick={() => setDeleteTarget(null)} type="button">
                No
              </button>
              <button
                className="btn danger-btn"
                data-testid="categories-confirm-delete"
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
