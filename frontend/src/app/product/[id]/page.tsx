"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useApp } from "@/src/providers/AppProvider";
import { ProductDetail } from "@/src/components/ProductDetail";
import type { CatalogProduct } from "@/src/types/catalog";
import { fetchProduct } from "@/src/lib/catalog";

export default function ProductPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { selectedProduct, setSelectedProduct, addToCart, openCart } = useApp();
  const [product, setProduct] = useState<CatalogProduct | null>(selectedProduct);
  const [loading, setLoading] = useState(!selectedProduct);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = params.id;
    if (!id) return;

    if (selectedProduct && String(selectedProduct.id) === String(id)) {
      setProduct(selectedProduct);
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const item = await fetchProduct(id);
        if (!cancelled) {
          setProduct(item);
          setSelectedProduct(item);
        }
      } catch {
        if (!cancelled) {
          setError("Artikel konnte nicht geladen werden.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [params.id, selectedProduct, setSelectedProduct]);

  const handleAddToCart = (item: CatalogProduct, qty: number) => {
    addToCart(item, qty);
    openCart();
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center gap-2 py-24 text-muted-foreground text-sm">
        <Loader2 size={18} className="animate-spin" />
        Artikel wird geladen…
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center space-y-4">
        <p className="text-destructive text-sm">{error ?? "Artikel nicht gefunden."}</p>
        <button
          onClick={() => router.replace("/")}
          className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold"
        >
          Zurück zum Shop
        </button>
      </div>
    );
  }

  return (
    <ProductDetail
      product={product}
      onBack={() => router.back()}
      onAddToCart={handleAddToCart}
    />
  );
}
