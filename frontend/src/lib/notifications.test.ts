import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as auth from "@/src/lib/auth";
import {
  fetchNotifications,
  markNotificationsSeen,
  type NotificationsResponse,
} from "@/src/lib/notifications";

const payload: NotificationsResponse = {
  unread_count: 1,
  results: [
    {
      kind: "order_paid",
      order_id: 1,
      order_number: "K39-2026-1000",
      occurred_at: "2026-01-01T00:00:00Z",
      message: "Zahlung erhalten",
      read: false,
    },
  ],
};

describe("notifications API", () => {
  beforeEach(() => {
    vi.spyOn(auth, "getAccessToken").mockReturnValue("test-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("fetchNotifications liest unread_count und results", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    await expect(fetchNotifications()).resolves.toEqual(payload);
  });

  it("markNotificationsSeen sendet POST", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await markNotificationsSeen();
    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/api/v1/accounts/user/mark-notifications-seen/"
    );
    expect((fetchMock.mock.calls[0][1] as RequestInit).method).toBe("POST");
  });
});
