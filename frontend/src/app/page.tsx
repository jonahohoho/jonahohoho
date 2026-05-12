"use client";

import { useCallback, useEffect, useState } from "react";
import FilterBar from "@/components/FilterBar";
import RentalCard from "@/components/RentalCard";
import ScrapeButton from "@/components/ScrapeButton";
import { Filters, Listing, ListingsResponse, SourceStats } from "@/types/listing";

const DEFAULT_FILTERS: Filters = {
  source: "",
  min_price: "",
  max_price: "",
  district: "",
  min_area: "",
  max_area: "",
  sort_by: "scraped_at_desc",
};

function buildQuery(filters: Filters, page: number) {
  const p = new URLSearchParams();
  if (filters.source) p.set("source", filters.source);
  if (filters.min_price) p.set("min_price", filters.min_price);
  if (filters.max_price) p.set("max_price", filters.max_price);
  if (filters.district) p.set("district", filters.district);
  if (filters.min_area) p.set("min_area", filters.min_area);
  if (filters.max_area) p.set("max_area", filters.max_area);
  p.set("sort_by", filters.sort_by);
  p.set("page", String(page));
  p.set("page_size", "24");
  return p.toString();
}

export default function Home() {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [listings, setListings] = useState<Listing[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<SourceStats[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);

  const fetchListings = useCallback(async (f: Filters, p: number) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/listings?${buildQuery(f, p)}`);
      if (!res.ok) throw new Error("fetch failed");
      const data: ListingsResponse = await res.json();
      setListings(data.listings);
      setTotal(data.total);
    } catch {
      // backend might not be running
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const [statsRes, distRes] = await Promise.all([
        fetch("/api/stats"),
        fetch("/api/districts"),
      ]);
      if (statsRes.ok) setStats(await statsRes.json());
      if (distRes.ok) setDistricts(await distRes.json());
    } catch {}
  }, []);

  useEffect(() => {
    fetchListings(filters, page);
  }, [filters, page, fetchListings]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const handleFilterChange = (f: Filters) => {
    setFilters(f);
    setPage(1);
  };

  const totalPages = Math.ceil(total / 24);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold text-gray-900">🏠 租屋聚合器</h1>
            <p className="text-xs text-gray-500">光寶中和廠 + 鳳三設計 雙通勤最佳化</p>
          </div>
          <ScrapeButton
            onDone={() => {
              fetchListings(filters, 1);
              fetchStats();
            }}
          />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-4 space-y-4">
        {/* Stats bar */}
        {stats.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {stats.map((s) => (
              <span
                key={s.source}
                className="bg-white border border-gray-200 rounded-full px-3 py-1 text-xs text-gray-600"
              >
                {s.source}: {s.count} 筆
              </span>
            ))}
            <span className="bg-blue-50 border border-blue-200 rounded-full px-3 py-1 text-xs text-blue-700 font-medium">
              共 {stats.reduce((a, s) => a + s.count, 0)} 筆
            </span>
          </div>
        )}

        {/* Commute legend */}
        <div className="flex gap-4 text-xs text-gray-500">
          <span>通勤時間：</span>
          <span className="text-green-700 font-semibold">≤15分 優</span>
          <span className="text-yellow-700 font-semibold">16-30分 可</span>
          <span className="text-red-600 font-semibold">&gt;30分 遠</span>
          <span className="text-gray-400">— 尚未計算</span>
        </div>

        {/* Filters */}
        <FilterBar filters={filters} districts={districts} onChange={handleFilterChange} />

        {/* Result count */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            {loading ? "載入中..." : `共 ${total} 筆物件`}
          </p>
          {total === 0 && !loading && (
            <p className="text-sm text-gray-400">
              還沒有資料，請點擊「抓取最新資料」
            </p>
          )}
        </div>

        {/* Grid */}
        {listings.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {listings.map((l) => (
              <RentalCard key={l.id} listing={l} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {listings.length === 0 && !loading && (
          <div className="text-center py-20 text-gray-400">
            <div className="text-5xl mb-4">🏠</div>
            <p className="text-lg">還沒有租屋資料</p>
            <p className="text-sm mt-1">點擊上方「抓取最新資料」開始</p>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 py-4">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm disabled:opacity-40 hover:bg-gray-50"
            >
              上一頁
            </button>
            <span className="px-3 py-1.5 text-sm text-gray-600">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm disabled:opacity-40 hover:bg-gray-50"
            >
              下一頁
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
