"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useApp } from "@/src/providers/AppProvider";
import { Checkout } from "@/src/components/Checkout";

function CheckoutContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const cancelled = searchParams.get("cancelled");
  const { cart, clearCart } = useApp();

  const handleFinish = () => {
    clearCart();
    router.push("/");
  };

  const handleConfirmed = () => {
    clearCart();
  };

  if (!sessionId && cart.length === 0) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center space-y-4">
        <p className="text-muted-foreground text-sm">
          {cancelled
            ? "Zahlung abgebrochen. Ihr Warenkorb ist leer."
            : "Ihr Warenkorb ist leer."}
        </p>
        <button
          onClick={() => router.push("/")}
          className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold"
        >
          Zurück zum Shop
        </button>
      </div>
    );
  }

  return (
    <Checkout
      cart={cart}
      onBack={() => router.back()}
      onFinish={handleFinish}
      onConfirmed={handleConfirmed}
      initialSessionId={sessionId}
    />
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={<div className="flex-1 py-16 text-center text-sm text-muted-foreground">Kasse wird geladen…</div>}>
      <CheckoutContent />
    </Suspense>
  );
}
