"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { ShopPage } from "@/src/components/ShopPage";
import { useApp } from "@/src/providers/AppProvider";
import type { CatalogProduct } from "@/src/types/catalog";

export function ShopPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeCategory = searchParams.get("category") ?? "all";
  const { addToCart, setSelectedProduct } = useApp();

  const handleCategoryChange = (cat: string) => {
    router.push(`/?category=${cat}`);
  };

  const handleProductClick = (product: CatalogProduct) => {
    setSelectedProduct(product);
    router.push(`/product/${product.id}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <ShopPage
      onAddToCart={(p) => addToCart(p)}
      activeCategory={activeCategory}
      onCategoryChange={handleCategoryChange}
      onProductClick={handleProductClick}
    />
  );
}
