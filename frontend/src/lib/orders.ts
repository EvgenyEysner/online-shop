import { apiFetch } from "@/src/lib/api";
import { getAccessToken } from "@/src/lib/auth";
import type { ConfirmedOrder } from "@/src/lib/checkout";
import type { PaginatedResponse } from "@/src/types/catalog";

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
