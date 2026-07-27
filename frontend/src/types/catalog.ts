export interface ProductSpec {
  label: string;
  value: string;
}

export interface CatalogCategory {
  id: number;
  name: string;
  slug: string;
  sublabel: string;
  image_url: string;
}

export interface CatalogProduct {
  id: number;
  name: string;
  description: string;
  price: number;
  originalPrice?: number;
  rating: number;
  reviews: number;
  badge?: string;
  category: string;
  watt?: string;
  image: string;
  specs: ProductSpec[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
