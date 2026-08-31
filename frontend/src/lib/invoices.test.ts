import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/src/lib/api";
import * as auth from "@/src/lib/auth";
import {
  downloadInvoicePdf,
  fetchMyInvoices,
  invoiceDownloadUrl,
  type Invoice,
} from "@/src/lib/invoices";

function makeInvoice(overrides: Partial<Invoice> = {}): Invoice {
  return {
    id: 7,
    invoice_number: "RE-2026-0001",
    document_type: "invoice",
    issued_at: "2026-01-01T00:00:00Z",
    net_amount: "100.00",
    tax_rate: "0.190",
    tax_amount: "19.00",
    total_amount: "119.00",
    sent_at: null,
    order: 1,
    ...overrides,
  };
}

describe("fetchMyInvoices", () => {
  beforeEach(() => {
    vi.spyOn(auth, "getAccessToken").mockReturnValue("test-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("gibt data.results einer paginierten Antwort zurück", async () => {
    const invoice = makeInvoice();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ count: 1, next: null, previous: null, results: [invoice] }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    await expect(fetchMyInvoices()).resolves.toEqual([invoice]);
  });
});

describe("invoiceDownloadUrl / downloadInvoicePdf", () => {
  beforeEach(() => {
    vi.spyOn(auth, "getAccessToken").mockReturnValue("test-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("baut die Download-URL ohne Slash-Verdopplung", () => {
    expect(invoiceDownloadUrl(7)).toMatch(/\/api\/v1\/orders\/invoices\/7\/download\/$/);
  });

  it("wirft ApiError bei fehlgeschlagenem Download", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("missing", { status: 404 }))
    );

    await expect(downloadInvoicePdf(7)).rejects.toBeInstanceOf(ApiError);
  });
});
