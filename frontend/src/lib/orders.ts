import { apiFetch } from "@/src/lib/api";
import { getAccessToken } from "@/src/lib/auth";
import type { ConfirmedOrder } from "@/src/lib/checkout";
import { fetchItemsByIds } from "@/src/lib/catalog";
import type { PaginatedResponse } from "@/src/types/catalog";
import type { AppContextValue } from "@/src/providers/AppProvider";

export type { ConfirmedOrder, ConfirmedOrderItem } from "@/src/lib/checkout";

export async function fetchMyOrders(): Promise<ConfirmedOrder[]> {
  const data = await apiFetch<PaginatedResponse<ConfirmedOrder> | ConfirmedOrder[]>(
    "/api/v1/orders/orders/?page_size=300",
    { method: "GET" },
    getAccessToken()
  );
  return Array.isArray(data) ? data : data.results;
}

export function formatOrderItemsSummary(order: ConfirmedOrder): string {
  return order.items
    .map((entry) => `${entry.item_name} × ${entry.quantity}`)
    .join(" + ");
}

export type SimplifiedOrderStatus = "pending" | "paid" | "failed" | "cancelled";

export const ORDER_STATUS_LABELS: Record<SimplifiedOrderStatus, string> = {
  pending: "Ausstehend",
  paid: "Bezahlt",
  failed: "Fehlgeschlagen",
  cancelled: "Storniert",
};

export function isActiveOrder(order: ConfirmedOrder): boolean {
  return order.payment_status === "pending" || order.payment_status === "paid";
}

export interface ReorderResult {
  addedCount: number;
  unavailable: string[];
}

// "Erneut bestellen" (siehe ADR 0020): lädt die aktuellen Artikeldaten
// per id__in nach (statt der historischen OrderItem-Snapshot-Felder) und
// legt nur tatsächlich verfügbare Artikel in den Warenkorb. Preis/Bestand
// kommen bewusst ausschließlich vom frisch geladenen Item, NICHT vom
// historischen OrderItem.unit_price - verhindert einen Nachkauf zu einem
// veralteten, ggf. günstigeren historischen Preis. Ein einzelner nicht
// mehr verfügbarer Artikel bricht den gesamten Vorgang nicht ab (B2).
export async function reorder(
  order: ConfirmedOrder,
  addToCart: AppContextValue["addToCart"]
): Promise<ReorderResult> {
  const ids = order.items
    .map((entry) => entry.item_id)
    .filter((id): id is number => id !== null);
  const current = await fetchItemsByIds(ids);

  const unavailable: string[] = [];
  let addedCount = 0;
  for (const orderItem of order.items) {
    const item =
      orderItem.item_id !== null
        ? current.find((c) => c.id === orderItem.item_id)
        : undefined;
    if (!item || (item.onStock ?? 0) <= 0) {
      unavailable.push(orderItem.item_name);
      continue;
    }
    const qty = Math.min(orderItem.quantity, item.onStock ?? 0);
    addToCart(item, qty);
    addedCount += 1;
  }

  return { addedCount, unavailable };
}
