import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as auth from "@/src/lib/auth";
import {
  deleteReview,
  fetchReviewsForItem,
  submitReview,
  type Review,
} from "@/src/lib/reviews";

const review: Review = {
  id: 4,
  item: 12,
  customer: "Max Kauf",
  customer_id: 2,
  rating: 5,
  comment: "top",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("reviews API", () => {
  beforeEach(() => {
    vi.spyOn(auth, "getAccessToken").mockReturnValue("test-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("fetchReviewsForItem filtert nach item", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ count: 1, next: null, previous: null, results: [review] }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchReviewsForItem(12)).resolves.toEqual([review]);
    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/api/v1/orders/reviews/?item=12"
    );
  });

  it("submitReview sendet item, rating und comment", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(review), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(submitReview(12, 5, "top")).resolves.toEqual(review);
    expect(JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body))).toEqual({
      item: 12,
      rating: 5,
      comment: "top",
    });
  });

  it("deleteReview ruft DELETE auf der Review-URL auf", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await deleteReview(4);
    expect(String(fetchMock.mock.calls[0][0])).toContain("/api/v1/orders/reviews/4/");
    expect((fetchMock.mock.calls[0][1] as RequestInit).method).toBe("DELETE");
  });
});
