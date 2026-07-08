"use client";

import { useRouter } from "next/navigation";
import { X, ShoppingCart, Trash2 } from "lucide-react";
import type { CartItem } from "@/providers/AppProvider";
import { useApp } from "@/providers/AppProvider";

interface CartDrawerProps {
  cart: CartItem[];
  onClose: () => void;
  onRemove: (id: number) => void;
}

export function CartDrawer({ cart, onClose, onRemove }: CartDrawerProps) {
  const router = useRouter();
  const total = cart.reduce((s, i) => s + i.price * i.qty * 1.19, 0);

  const handleCheckout = () => {
    onClose();
    router.push("/checkout");
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-card w-full max-w-sm h-full shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div
            className="flex items-center gap-2 text-foreground font-bold"
            style={{ fontFamily: "var(--font-display)" }}
          >
            <ShoppingCart size={18} className="text-accent" />
            Warenkorb ({cart.reduce((s, i) => s + i.qty, 0)})
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-muted text-muted-foreground"
          >
            <X size={18} />
          </button>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {cart.length === 0 ? (
            <div className="text-center text-muted-foreground text-sm py-12">
              <ShoppingCart size={36} className="mx-auto mb-3 opacity-30" />
              Ihr Warenkorb ist leer
            </div>
          ) : (
            cart.map((item) => (
              <div
                key={item.id}
                className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg border border-border"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-foreground text-xs font-semibold leading-snug mb-0.5">
                    {item.name}
                  </p>
                  <p className="text-muted-foreground text-xs">Menge: {item.qty}</p>
                  <p
                    className="text-accent font-bold text-sm mt-1"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    {(item.price * item.qty * 1.19).toLocaleString("de-DE", {
                      style: "currency",
                      currency: "EUR",
                    })}
                  </p>
                </div>
                <button
                  onClick={() => onRemove(item.id)}
                  className="p-1.5 text-muted-foreground hover:text-destructive transition-colors shrink-0"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {cart.length > 0 && (
          <div className="px-5 py-4 border-t border-border space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-foreground font-semibold text-sm">
                Gesamt (inkl. MwSt.)
              </span>
              <span
                className="text-foreground font-bold"
                style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem" }}
              >
                {total.toLocaleString("de-DE", {
                  style: "currency",
                  currency: "EUR",
                })}
              </span>
            </div>
            <button
              onClick={handleCheckout}
              className="w-full py-3 bg-accent text-primary font-bold rounded-lg hover:bg-accent/90 transition-colors"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Zur Kasse →
            </button>
            <button
              onClick={onClose}
              className="w-full py-2.5 border border-border text-muted-foreground text-sm rounded-lg hover:bg-muted transition-colors"
            >
              Weiter einkaufen
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
