"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { createMovement, getBatches, getProducts } from "@/lib/api";
import { useRequiredToken } from "@/components/use-required-token";

export default function NewMovementPage() {
  const token = useRequiredToken();
  const router = useRouter();
  const [productId, setProductId] = useState("");
  const [batchId, setBatchId] = useState("");
  const [movementType, setMovementType] = useState<"in" | "out" | "adjustment">("in");
  const [quantity, setQuantity] = useState(1);
  const [adjustmentMode, setAdjustmentMode] = useState<"increase" | "decrease">("increase");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const productsQuery = useQuery({
    queryKey: ["movement-products"],
    queryFn: () => getProducts(token as string, 0, 100),
    enabled: Boolean(token)
  });

  const batchesQuery = useQuery({
    queryKey: ["movement-batches", productId],
    queryFn: () => getBatches(token as string, 0, 100, productId),
    enabled: Boolean(token && productId)
  });

  const productOptions = useMemo(() => productsQuery.data?.items ?? [], [productsQuery.data]);
  const batchOptions = useMemo(() => batchesQuery.data?.items ?? [], [batchesQuery.data]);

  useEffect(() => {
    if (!productId) {
      setBatchId("");
      return;
    }
    if (batchOptions.length === 0) {
      setBatchId("");
      return;
    }
    const exists = batchOptions.some((batch) => batch.id === batchId);
    if (!exists) {
      setBatchId(batchOptions[0].id);
    }
  }, [productId, batchOptions, batchId]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    if (!productId.trim()) {
      setError("Product ID is required.");
      return;
    }
    if (!batchId.trim()) {
      setError("Batch ID is required.");
      return;
    }
    setPending(true);
    setError(null);
    try {
      await createMovement(token, {
        product_id: productId.trim(),
        batch_id: batchId.trim(),
        movement_type: movementType,
        quantity,
        adjustment_mode: movementType === "adjustment" ? adjustmentMode : undefined,
        reason: reason.trim() || undefined
      });
      router.replace("/inventory");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create movement");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="container" style={{ maxWidth: 620 }}>
      <div className="card col">
        <h1>Stock Count & Movement</h1>
        <form className="col" onSubmit={onSubmit} data-testid="movement-form">
          <label>Product</label>
          <select
            data-testid="movement-product-id"
            value={productId}
            onChange={(e) => {
              setProductId(e.target.value);
              setError(null);
            }}
            required
          >
            <option value="">Select product</option>
            {productOptions.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name} ({product.sku})
              </option>
            ))}
          </select>
          <label>Batch ID</label>
          <select
            data-testid="movement-batch-id"
            value={batchId}
            onChange={(e) => {
              setBatchId(e.target.value);
              setError(null);
            }}
            disabled={!productId || batchesQuery.isLoading}
            required
          >
            <option value="">
              {productId ? (batchesQuery.isLoading ? "Loading batches..." : "Select batch") : "Select product first"}
            </option>
            {batchOptions.map((batch) => (
              <option key={batch.id} value={batch.id}>
                {batch.id}
              </option>
            ))}
          </select>
          {productsQuery.error && <div className="danger">{(productsQuery.error as Error).message}</div>}
          {batchesQuery.error && <div className="danger">{(batchesQuery.error as Error).message}</div>}
          <label>Movement Type</label>
          <select data-testid="movement-type" value={movementType} onChange={(e) => setMovementType(e.target.value as "in" | "out" | "adjustment")}>
            <option value="in">in</option>
            <option value="out">out</option>
            <option value="adjustment">adjustment</option>
          </select>
          {movementType === "adjustment" && (
            <>
              <label>Adjustment Mode</label>
              <select data-testid="movement-adjustment-mode" value={adjustmentMode} onChange={(e) => setAdjustmentMode(e.target.value as "increase" | "decrease")}>
                <option value="increase">increase</option>
                <option value="decrease">decrease</option>
              </select>
            </>
          )}
          <label>Quantity</label>
          <input data-testid="movement-quantity" min={1} type="number" value={quantity} onChange={(e) => setQuantity(Number(e.target.value))} required />
          <label>Reason</label>
          <input data-testid="movement-reason" value={reason} onChange={(e) => setReason(e.target.value)} />
          {error && <div className="danger" data-testid="movement-error">{error}</div>}
          <div className="row">
            <button className="btn" data-testid="movement-submit" disabled={pending} type="submit">
              {pending ? "Saving..." : "Save"}
            </button>
            <button
              className="btn secondary"
              data-testid="movement-cancel"
              disabled={pending}
              onClick={() => router.push("/inventory")}
              type="button"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
