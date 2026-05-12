export interface Listing {
  id: number;
  source: string;
  title: string;
  price: number | null;
  address: string | null;
  district: string | null;
  city: string | null;
  area_ping: number | null;
  rooms: string | null;
  floor: string | null;
  url: string;
  image_url: string | null;
  lat: number | null;
  lng: number | null;
  commute_min_guangbao: number | null;
  commute_min_fengsan: number | null;
  scraped_at: string | null;
}

export interface ListingsResponse {
  total: number;
  page: number;
  page_size: number;
  listings: Listing[];
}

export interface SourceStats {
  source: string;
  count: number;
  last_scraped: string | null;
}

export interface ScrapeResult {
  source: string;
  inserted: number;
  errors: number;
}

export interface Filters {
  source: string;
  min_price: string;
  max_price: string;
  district: string;
  min_area: string;
  max_area: string;
  sort_by: string;
}
