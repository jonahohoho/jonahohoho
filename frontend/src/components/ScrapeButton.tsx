"use client";

import { useState } from "react";
import { ScrapeResult } from "@/types/listing";

interface Props {
  onDone: () => void;
}

export default function ScrapeButton({ onDone }: Props) {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ScrapeResult[] | null>(null);

  const run = async () => {
    setLoading(true);
    setResults(null);
    try {
      const res = await fetch("/api/scrape", { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      const data: ScrapeResult[] = await res.json();
      setResults(data);
      onDone();
    } catch (e) {
      console.error(e);
      alert("抓取失敗，請確認後端是否啟動");
    } finally {
      setLoading(false);
    }
  };

  const total = results?.reduce((s, r) => s + r.inserted, 0) ?? 0;

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={run}
        disabled={loading}
        className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
      >
        {loading ? (
          <>
            <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            抓取中...
          </>
        ) : (
          "抓取最新資料"
        )}
      </button>

      {results && !loading && (
        <span className="text-sm text-gray-600">
          新增 <strong>{total}</strong> 筆 ·{" "}
          {results.map((r) => `${r.source}+${r.inserted}`).join(" ")}
        </span>
      )}
    </div>
  );
}
