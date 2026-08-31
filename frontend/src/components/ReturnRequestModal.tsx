"use client";

import { FormEvent, useState } from "react";
import { Loader2, Minus, Plus, RotateCcw, X } from "lucide-react";
import { ApiError } from "@/src/lib/api";
import type { ConfirmedOrder } from "@/src/lib/checkout";
import { createReturnRequest, type ReturnRequest } from "@/src/lib/returns";

interface ReturnRequestModalProps {
  order: ConfirmedOrder;
  onClose: () => void;
  onSubmitted: (returnRequest: ReturnRequest) => void;
}

interface SelectedItem {
  checked: boolean;
  quantity: number;
}

export function ReturnRequestModal({ order, onClose, onSubmitted }: ReturnRequestModalProps) {
  const [selected, setSelected] = useState<Record<number, SelectedItem>>(() =>
    Object.fromEntries(
      order.items.map((item) => [item.id, { checked: false, quantity: 1 }])
    )
  );
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleItem = (itemId: number) => {
    setSelected((current) => ({
      ...current,
      [itemId]: { ...current[itemId], checked: !current[itemId].checked },
    }));
  };

  const changeQuantity = (itemId: number, delta: number, max: number) => {
    setSelected((current) => {
      const next = Math.min(Math.max(current[itemId].quantity + delta, 1), max);
      return { ...current, [itemId]: { ...current[itemId], quantity: next } };
    });
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    const items = order.items
      .filter((item) => selected[item.id]?.checked)
      .map((item) => ({
        order_item: item.id,
        quantity: selected[item.id].quantity,
      }));

    if (items.length === 0) {
      setError("Bitte wählen Sie mindestens einen Artikel aus.");
      return;
    }
    if (!reason.trim()) {
      setError("Bitte geben Sie einen Grund für die Rückgabe an.");
      return;
    }

    setIsSubmitting(true);
    try {
      const returnRequest = await createReturnRequest({
        order: order.id,
        reason: reason.trim(),
        items,
      });
      onSubmitted(returnRequest);
      onClose();
    } catch (err) {
      const message =
        err instanceof ApiError
          ? [...err.generalErrors, ...Object.values(err.fieldErrors).flat()].join(" ") ||
            err.message
          : "Rückgabe konnte nicht angefragt werden. Bitte versuchen Sie es erneut.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-card border border-border rounded-2xl w-full max-w-md shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-primary flex items-center justify-center">
              <RotateCcw size={15} className="text-accent" />
            </div>
            <div>
              <div
                className="text-foreground font-bold leading-none"
                style={{ fontFamily: "var(--font-display)", fontSize: "0.95rem" }}
              >
                Rückgabe anfragen
              </div>
              <div className="text-muted-foreground leading-none" style={{ fontSize: "0.6rem" }}>
                Bestellung {order.order_number}
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded hover:bg-muted text-muted-foreground"
            disabled={isSubmitting}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="text-foreground text-sm font-semibold block mb-2">
              Welche Artikel möchten Sie zurückgeben?
            </label>
            <div className="space-y-2">
              {order.items.map((item) => {
                const state = selected[item.id];
                return (
                  <div
                    key={item.id}
                    className="flex items-center gap-3 p-3 bg-muted/20 border border-border rounded-lg"
                  >
                    <input
                      type="checkbox"
                      checked={state.checked}
                      onChange={() => toggleItem(item.id)}
                      disabled={isSubmitting}
                      className="rounded border-border shrink-0"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-foreground text-sm font-medium truncate">
                        {item.item_name}
                      </div>
                      <div className="text-muted-foreground text-xs">
                        Bestellt: {item.quantity} Stück
                      </div>
                    </div>
                    {state.checked && (
                      <div className="flex items-center gap-1.5 shrink-0">
                        <button
                          type="button"
                          onClick={() => changeQuantity(item.id, -1, item.quantity)}
                          disabled={isSubmitting || state.quantity <= 1}
                          className="w-6 h-6 rounded border border-border flex items-center justify-center text-foreground disabled:opacity-40"
                        >
                          <Minus size={12} />
                        </button>
                        <span className="text-foreground text-sm font-semibold w-6 text-center">
                          {state.quantity}
                        </span>
                        <button
                          type="button"
                          onClick={() => changeQuantity(item.id, 1, item.quantity)}
                          disabled={isSubmitting || state.quantity >= item.quantity}
                          className="w-6 h-6 rounded border border-border flex items-center justify-center text-foreground disabled:opacity-40"
                        >
                          <Plus size={12} />
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <label
              htmlFor="return-reason"
              className="text-foreground text-sm font-semibold block mb-1.5"
            >
              Grund für die Rückgabe
            </label>
            <textarea
              id="return-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
              rows={3}
              maxLength={500}
              disabled={isSubmitting}
              placeholder="z. B. Artikel entspricht nicht der Beschreibung, defekt, nicht mehr benötigt …"
              className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-60 resize-none"
            />
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-xs text-destructive">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-primary text-primary-foreground font-bold rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {isSubmitting ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Wird gesendet …
              </>
            ) : (
              "Rückgabe anfragen"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
