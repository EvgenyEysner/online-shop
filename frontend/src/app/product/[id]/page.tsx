"use client";

import { useRouter } from "next/navigation";
import { useApp } from "@/src/providers/AppProvider";
import { ProductDetail } from "@/src/components/ProductDetail";
import type { ProductDetailData } from "@/src/components/ProductDetail";

export default function ProductPage() {
  const router = useRouter();
  const { selectedProduct, addToCart, openCart } = useApp();

  if (!selectedProduct) {
    // Fallback if user navigated directly via URL
    router.replace("/");
    return null;
  }

  const handleAddToCart = (product: ProductDetailData, qty: number) => {
    addToCart(product, qty);
    openCart();
  };

  return (
    <ProductDetail
      product={selectedProduct}
      onBack={() => router.back()}
      onAddToCart={handleAddToCart}
    />
  );
}
