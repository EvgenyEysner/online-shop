import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/src/lib/api";
import * as auth from "@/src/lib/auth";
import * as catalog from "@/src/lib/catalog";
import {
  fetchMyOrders,
  formatOrderItemsSummary,
  isActiveOrder,
  reorder,
  type ConfirmedOrder,
  type ConfirmedOrderItem,
} from "@/src/lib/orders";
import type { CatalogProduct } from "@/src/types/catalog";

function makeOrder(overrides: Partial<ConfirmedOrder> = {}): ConfirmedOrder {
  return {
    id: 1,
    order_number: "ORD-1",
    email: "test@example.com",
    phone: "",
    note: null,
    shipping_salutation: "",
    shipping_first_name: "Max",
    shipping_last_name: "Mustermann",
    shipping_company: "",
    shipping_street: "Musterstr.",
    shipping_street_no: "1",
    shipping_zip: "12345",
    shipping_city: "Berlin",
    shipping_country: "DE",
    payment_method: "card",
    payment_status: "paid",
    subtotal: "10.00",
    tax_amount: "1.90",
    shipping_cost: "0.00",
    total: "11.90",
    items: [],
    created_at: "2026-01-01T00:00:00Z",
    paid_at: "2026-01-01T00:05:00Z",
    fulfillment_status: "pending",
    tracking_number: "",
    carrier: "",
    shipped_at: null,
    delivered_at: null,
    has_invoice: false,
    can_request_return: false,
    ...overrides,
  };
}

function makeItem(overrides: Partial<ConfirmedOrderItem> = {}): ConfirmedOrderItem {
  return {
    id: 1,
    item: "1",
    item_id: 1,
    item_name: "Solarmodul",
    unit_price: "100.00",
    quantity: 1,
    line_total: "100.00",
    ...overrides,
  };
}

describe("fetchMyOrders", () => {
  beforeEach(() => {
    vi.spyOn(auth, "getAccessToken").mockReturnValue("test-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("ruft den Bestell-Endpoint mit Bearer-Token und page_size=300 auf", async () => {
    const order = makeOrder();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ count: 1, next: null, previous: null, results: [order] }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchMyOrders();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/api/v1/orders/orders/?page_size=300");
    const headers = new Headers((options as RequestInit).headers);
    expect(headers.get("Authorization")).toBe("Bearer test-token");
  });

  it("gibt data.results zurück, wenn die API eine paginierte Antwort liefert", async () => {
    const order = makeOrder();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ count: 1, next: null, previous: null, results: [order] }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchMyOrders();

    expect(result).toEqual([order]);
  });

  it("gibt die Antwort direkt zurück, wenn die API ein rohes Array liefert", async () => {
    const orders = [makeOrder({ id: 1 }), makeOrder({ id: 2 })];
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(orders), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchMyOrders();

    expect(result).toEqual(orders);
  });

  it("wirft einen ApiError, wenn die API einen Fehlerstatus liefert", async () => {
    const fetchMock = vi.fn().mockImplementation(
      async () =>
        new Response(JSON.stringify({ detail: "Nicht autorisiert" }), {
          status: 401,
          statusText: "Unauthorized",
          headers: { "Content-Type": "application/json" },
        })
    );
    vi.stubGlobal("fetch", fetchMock);

    let caught: unknown;
    try {
      await fetchMyOrders();
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(ApiError);
    expect(caught).toMatchObject({ status: 401, message: "Nicht autorisiert" });
  });
});

describe("formatOrderItemsSummary", () => {
  it("verkettet mehrere Items korrekt mit ' + ' und dem '×'-Format", () => {
    const order = makeOrder({
      items: [
        makeItem({ item_name: "Solarmodul", quantity: 2 }),
        makeItem({ item_name: "Kabel", quantity: 1 }),
      ],
    });

    expect(formatOrderItemsSummary(order)).toBe("Solarmodul × 2 + Kabel × 1");
  });

  it("liefert einen leeren String bei einer Order ohne Items", () => {
    const order = makeOrder({ items: [] });

    expect(formatOrderItemsSummary(order)).toBe("");
  });
});

describe("reorder", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("legt nur verfügbare Artikel in den Warenkorb und listet fehlende", async () => {
    const available: CatalogProduct = {
      id: 1,
      name: "Solarmodul",
      description: "",
      price: 199,
      rating: 0,
      reviews: 0,
      category: "solar",
      image: "",
      specs: [],
      onStock: 1,
    };
    vi.spyOn(catalog, "fetchItemsByIds").mockResolvedValue([available]);
    const addToCart = vi.fn();

    const result = await reorder(
      makeOrder({
        items: [
          makeItem({ item_id: 1, item_name: "Solarmodul", quantity: 3 }),
          makeItem({ id: 2, item_id: 2, item_name: "Kabel", quantity: 1 }),
        ],
      }),
      addToCart
    );

    expect(addToCart).toHaveBeenCalledTimes(1);
    expect(addToCart).toHaveBeenCalledWith(available, 1);
    expect(result).toEqual({ addedCount: 1, unavailable: ["Kabel"] });
  });

  it("behandelt eine leere Bestellung ohne API-Aufruf-Fehler", async () => {
    vi.spyOn(catalog, "fetchItemsByIds").mockResolvedValue([]);
    const addToCart = vi.fn();

    const result = await reorder(makeOrder({ items: [] }), addToCart);

    expect(addToCart).not.toHaveBeenCalled();
    expect(result).toEqual({ addedCount: 0, unavailable: [] });
  });
});

describe("isActiveOrder", () => {
  it.each(["pending", "paid"])(
    "liefert true für payment_status '%s'",
    (status) => {
      expect(isActiveOrder(makeOrder({ payment_status: status }))).toBe(true);
    }
  );

  it.each(["failed", "cancelled"])(
    "liefert false für payment_status '%s'",
    (status) => {
      expect(isActiveOrder(makeOrder({ payment_status: status }))).toBe(false);
    }
  );
});
