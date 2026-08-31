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
  // Nur von fetchItemsByIds() befüllt (Reorder, siehe ADR 0020) - normale
  // Katalogabrufe (fetchProducts/fetchProduct) filtern serverseitig
  // bereits auf on_stock > 0 und benötigen den Wert selbst nicht.
  onStock?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
