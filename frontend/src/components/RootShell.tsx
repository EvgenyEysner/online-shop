"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Navbar } from "@/src/components/Navbar";
import { Footer } from "@/src/components/Footer";
import { CartDrawer } from "@/src/components/CartDrawer";
import { LoginModal } from "@/src/components/LoginModal";
import { OfflineBanner } from "@/src/components/OfflineBanner";
import { PWAInstallBanner } from "@/src/components/PWAInstallBanner";
import { useApp } from "@/src/providers/AppProvider";

export function RootShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const {
    cartCount,
    openCart,
    openLogin,
    isLoggedIn,
    showCart,
    closeCart,
    cart,
    removeFromCart,
    showLogin,
    closeLogin,
    login,
  } = useApp();

  const isDashboard = pathname === "/dashboard";
  const isCheckout = pathname === "/checkout";

  const showNavbar = !isDashboard;
  const showFooter = !isDashboard && !isCheckout;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <OfflineBanner />

      {showNavbar && (
        <Navbar
          cartCount={cartCount}
          onCartClick={openCart}
          onLoginClick={openLogin}
          isLoggedIn={isLoggedIn}
        />
      )}

      <main className="flex-1">{children}</main>

      {showFooter && <Footer />}

      {showCart && (
        <CartDrawer
          cart={cart}
          onClose={closeCart}
          onRemove={removeFromCart}
        />
      )}

      {showLogin && (
        <LoginModal onClose={closeLogin} onLogin={login} />
      )}

      <PWAInstallBanner />
    </div>
  );
}
