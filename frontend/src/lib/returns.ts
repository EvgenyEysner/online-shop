import { apiFetch } from "@/src/lib/api";
import { getAccessToken } from "@/src/lib/auth";
import type { PaginatedResponse } from "@/src/types/catalog";

export type ReturnRequestStatus = "requested" | "approved" | "rejected" | "refunded";

export interface ReturnRequestItem {
  id: number;
  order_item: number;
  item_name: string;
  quantity: number;
}

export interface ReturnRequest {
  id: number;
  order: number;
  status: ReturnRequestStatus;
  reason: string;
  requested_at: string;
  decided_at: string | null;
  rejection_note: string;
  refunded_at: string | null;
  items: ReturnRequestItem[];
}

export const RETURN_REQUEST_STATUS_LABELS: Record<ReturnRequestStatus, string> = {
  requested: "Rückgabe angefragt",
  approved: "Rückgabe genehmigt",
  rejected: "Rückgabe abgelehnt",
  refunded: "Rückgabe erstattet",
};

export interface CreateReturnRequestPayload {
  order: number;
  reason: string;
  items: Array<{ order_item: number; quantity: number }>;
}

export async function fetchMyReturnRequests(): Promise<ReturnRequest[]> {
  const data = await apiFetch<PaginatedResponse<ReturnRequest> | ReturnRequest[]>(
    "/api/v1/orders/return-requests/?page_size=300",
    { method: "GET" },
    getAccessToken()
  );
  return Array.isArray(data) ? data : data.results;
}

export async function createReturnRequest(
  payload: CreateReturnRequestPayload
): Promise<ReturnRequest> {
  return apiFetch<ReturnRequest>(
    "/api/v1/orders/return-requests/",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    getAccessToken()
  );
}
