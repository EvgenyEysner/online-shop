import { apiFetch } from "@/src/lib/api";
import { getAccessToken } from "@/src/lib/auth";

export type PaymentMethod = "bank" | "invoice" | "card" | "paypal";

export interface CheckoutAddress {
  salutation?: string;
  first_name: string;
  last_name: string;
  company?: string;
  street: string;
  street_no?: string;
  zip: string;
  city: string;
  country?: string;
}

export interface CreateCheckoutSessionPayload {
  email: string;
  phone?: string;
  note?: string;
  payment_method: PaymentMethod;
  items: Array<{ item: number; quantity: number }>;
  shipping: CheckoutAddress;
  billing?: CheckoutAddress;
  billing_same_as_shipping: boolean;
}

export interface CreateCheckoutSessionResponse {
  session_id: string;
  url: string;
  draft_id: string;
  public_key: string;
}

export interface ConfirmedOrderItem {
  id: number;
  item: string | null;
  item_name: string;
  unit_price: string;
  quantity: number;
  line_total: string;
}

export interface ConfirmedOrder {
  id: number;
  order_number: string;
  email: string;
  phone: string;
  note: string | null;
  shipping_salutation: string;
  shipping_first_name: string;
  shipping_last_name: string;
  shipping_company: string;
  shipping_street: string;
  shipping_street_no: string;
  shipping_zip: string;
  shipping_city: string;
  shipping_country: string;
  payment_method: PaymentMethod;
  payment_status: string;
  subtotal: string;
  tax_amount: string;
  shipping_cost: string;
  total: string;
  items: ConfirmedOrderItem[];
  created_at: string;
}

export async function createCheckoutSession(
  payload: CreateCheckoutSessionPayload
): Promise<CreateCheckoutSessionResponse> {
  return apiFetch<CreateCheckoutSessionResponse>(
    "/api/v1/orders/checkout/create-session/",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    getAccessToken()
  );
}

export async function confirmCheckoutSession(
  sessionId: string
): Promise<ConfirmedOrder> {
  const params = new URLSearchParams({ session_id: sessionId });
  return apiFetch<ConfirmedOrder>(
    `/api/v1/orders/checkout/confirm/?${params.toString()}`,
    { method: "GET" },
    getAccessToken()
  );
}
