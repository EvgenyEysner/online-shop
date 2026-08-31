import { apiFetch } from "@/src/lib/api";
import { getAccessToken } from "@/src/lib/auth";
import type { PaginatedResponse } from "@/src/types/catalog";

export interface Review {
  id: number;
  item: number;
  customer: string;
  customer_id: number;
  rating: number;
  comment: string;
  created_at: string;
  updated_at: string;
}

export async function fetchReviewsForItem(itemId: number | string): Promise<Review[]> {
  const data = await apiFetch<PaginatedResponse<Review> | Review[]>(
    `/api/v1/orders/reviews/?item=${itemId}&page_size=300`,
    { method: "GET" },
    getAccessToken()
  );
  return Array.isArray(data) ? data : data.results;
}

export async function submitReview(
  itemId: number | string,
  rating: number,
  comment: string
): Promise<Review> {
  return apiFetch<Review>(
    "/api/v1/orders/reviews/",
    {
      method: "POST",
      body: JSON.stringify({ item: itemId, rating, comment }),
    },
    getAccessToken()
  );
}

export async function deleteReview(reviewId: number): Promise<void> {
  await apiFetch<void>(
    `/api/v1/orders/reviews/${reviewId}/`,
    { method: "DELETE" },
    getAccessToken()
  );
}
