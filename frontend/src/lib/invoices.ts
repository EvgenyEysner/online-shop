import { apiFetch, ApiError, getApiBaseUrl } from "@/src/lib/api";
import { getAccessToken } from "@/src/lib/auth";
import type { PaginatedResponse } from "@/src/types/catalog";

export interface Invoice {
  id: number;
  invoice_number: string;
  document_type: string;
  issued_at: string;
  net_amount: string;
  tax_rate: string;
  tax_amount: string;
  total_amount: string;
  sent_at: string | null;
  order: number;
}

export async function fetchMyInvoices(): Promise<Invoice[]> {
  const data = await apiFetch<PaginatedResponse<Invoice> | Invoice[]>(
    "/api/v1/orders/invoices/?page_size=300",
    { method: "GET" },
    getAccessToken()
  );
  return Array.isArray(data) ? data : data.results;
}

export function invoiceDownloadUrl(invoiceId: number): string {
  return `${getApiBaseUrl()}/api/v1/orders/invoices/${invoiceId}/download/`;
}

// Der Download-Endpoint erfordert IsAuthenticated (Bearer-Token) - ein
// normaler <a href>-Link würde keinen Authorization-Header senden. Daher
// laden wir das PDF per fetch(), erzeugen daraus eine Object-URL und lösen
// darüber einen programmatischen Download-Klick aus.
export async function downloadInvoicePdf(invoiceId: number): Promise<void> {
  const token = getAccessToken();
  const response = await fetch(invoiceDownloadUrl(invoiceId), {
    method: "GET",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new ApiError(
      "Rechnung konnte nicht heruntergeladen werden.",
      response.status
    );
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const filenameMatch = disposition.match(/filename="?([^";]+)"?/);
  const filename = filenameMatch ? filenameMatch[1] : `${invoiceId}.pdf`;

  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(objectUrl);
}
