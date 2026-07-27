import { apiFetch } from "@/src/lib/api";
import type {
  CatalogCategory,
  CatalogProduct,
  PaginatedResponse,
  ProductSpec,
} from "@/src/types/catalog";

interface ApiItem {
  id: number;
  name: string;
  description: string | null;
  image: string;
  category: string | null;
  price: string | number;
  original_price: string | number | null;
  watt: string;
  badge: string;
  rating: string | number;
  reviews: number;
  specs: ProductSpec[];
}

function toNumber(value: string | number | null | undefined): number | undefined {
  if (value === null || value === undefined || value === "") return undefined;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : undefined;
}

export function mapApiItem(item: ApiItem): CatalogProduct {
  const originalPrice = toNumber(item.original_price);
  return {
    id: item.id,
    name: item.name,
    description: item.description ?? "",
    price: toNumber(item.price) ?? 0,
    originalPrice,
    rating: toNumber(item.rating) ?? 0,
    reviews: item.reviews ?? 0,
    badge: item.badge || undefined,
    category: item.category ?? "",
    watt: item.watt || undefined,
    image: item.image,
    specs: Array.isArray(item.specs) ? item.specs : [],
  };
}

export async function fetchCategories(): Promise<CatalogCategory[]> {
  const data = await apiFetch<CatalogCategory[] | PaginatedResponse<CatalogCategory>>(
    "/api/v1/orders/categories/"
  );
  return Array.isArray(data) ? data : data.results;
}

export async function fetchProducts(categorySlug?: string): Promise<CatalogProduct[]> {
  const params = new URLSearchParams({ page_size: "300" });
  const data = await apiFetch<PaginatedResponse<ApiItem> | ApiItem[]>(
    `/api/v1/orders/items/?${params.toString()}`
  );
  const items = Array.isArray(data) ? data : data.results;
  const products = items.map(mapApiItem);
  if (!categorySlug || categorySlug === "all") return products;
  return products.filter((p) => p.category === categorySlug);
}

export async function fetchProduct(id: number | string): Promise<CatalogProduct> {
  const item = await apiFetch<ApiItem>(`/api/v1/orders/items/${id}/`);
  return mapApiItem(item);
}
