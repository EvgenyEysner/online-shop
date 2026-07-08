"use client";

import { useRouter } from "next/navigation";
import { useApp } from "@/src/providers/AppProvider";
import { Checkout } from "@/src/components/Checkout";

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, clearCart } = useApp();

  const handleFinish = () => {
    clearCart();
    router.push("/");
  };

  return (
    <Checkout
      cart={cart}
      onBack={() => router.back()}
      onFinish={handleFinish}
    />
  );
}
