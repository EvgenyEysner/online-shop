import { apiFetch } from "@/src/lib/api";
import { getAccessToken } from "@/src/lib/auth";

export type NotificationKind =
  | "order_created"
  | "order_paid"
  | "order_shipped"
  | "order_delivered"
  | "invoice_issued"
  | "return_status_changed";

export interface NotificationEvent {
  kind: NotificationKind;
  order_id: number;
  order_number: string;
  occurred_at: string;
  message: string;
  read: boolean;
}

export interface NotificationsResponse {
  results: NotificationEvent[];
  unread_count: number;
}

export async function fetchNotifications(): Promise<NotificationsResponse> {
  return apiFetch<NotificationsResponse>(
    "/api/v1/orders/notifications/",
    { method: "GET" },
    getAccessToken()
  );
}

export async function markNotificationsSeen(): Promise<void> {
  await apiFetch<void>(
    "/api/v1/accounts/user/mark-notifications-seen/",
    { method: "POST" },
    getAccessToken()
  );
}
