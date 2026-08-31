import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as auth from "@/src/lib/auth";
import {
  createReturnRequest,
  fetchMyReturnRequests,
  type ReturnRequest,
} from "@/src/lib/returns";

const request: ReturnRequest = {
  id: 1,
  order: 9,
  status: "requested",
  reason: "Widerruf",
  requested_at: "2026-01-01T00:00:00Z",
  decided_at: null,
  rejection_note: "",
  refunded_at: null,
  items: [{ id: 1, order_item: 3, item_name: "Solarmodul", quantity: 1 }],
};

describe("returns API", () => {
  beforeEach(() => {
    vi.spyOn(auth, "getAccessToken").mockReturnValue("test-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("fetchMyReturnRequests liest paginierte results", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ count: 1, next: null, previous: null, results: [request] }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchMyReturnRequests()).resolves.toEqual([request]);
    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/api/v1/orders/return-requests/?page_size=300"
    );
  });

  it("createReturnRequest sendet den Payload per POST", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(request), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const payload = {
      order: 9,
      reason: "Widerruf",
      items: [{ order_item: 3, quantity: 1 }],
    };
    await expect(createReturnRequest(payload)).resolves.toEqual(request);

    const [, options] = fetchMock.mock.calls[0];
    expect((options as RequestInit).method).toBe("POST");
    expect(JSON.parse(String((options as RequestInit).body))).toEqual(payload);
  });
});
