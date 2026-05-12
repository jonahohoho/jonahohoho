"use client";

import { Filters } from "@/types/listing";

interface Props {
  filters: Filters;
  districts: string[];
  onChange: (f: Filters) => void;
}

const SOURCES = [
  { value: "", label: "全部來源" },
  { value: "rental123", label: "好租123" },
  { value: "houseprice", label: "好房網" },
  { value: "tmm", label: "崔媽媽" },
  { value: "ptt", label: "PTT" },
];

const SORT_OPTIONS = [
  { value: "scraped_at_desc", label: "最新上架" },
  { value: "price_asc", label: "價格低到高" },
  { value: "price_desc", label: "價格高到低" },
  { value: "commute_guangbao", label: "光寶通勤最短" },
  { value: "commute_fengsan", label: "鳳三通勤最短" },
];

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <label className="text-xs text-gray-500">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border border-gray-300 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function NumberInput({
  label,
  value,
  placeholder,
  onChange,
}: {
  label: string;
  value: string;
  placeholder: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <label className="text-xs text-gray-500">{label}</label>
      <input
        type="number"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="border border-gray-300 rounded-lg px-2 py-1.5 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
  );
}

export default function FilterBar({ filters, districts, onChange }: Props) {
  const set = (key: keyof Filters) => (v: string) => onChange({ ...filters, [key]: v });

  const districtOptions = [
    { value: "", label: "全部地區" },
    ...districts.map((d) => ({ value: d, label: d })),
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-3 flex flex-wrap gap-3 items-end">
      <Select label="來源" value={filters.source} options={SOURCES} onChange={set("source")} />
      <Select
        label="地區"
        value={filters.district}
        options={districtOptions}
        onChange={set("district")}
      />
      <NumberInput label="最低租金" value={filters.min_price} placeholder="5000" onChange={set("min_price")} />
      <NumberInput label="最高租金" value={filters.max_price} placeholder="30000" onChange={set("max_price")} />
      <NumberInput label="最小坪數" value={filters.min_area} placeholder="8" onChange={set("min_area")} />
      <NumberInput label="最大坪數" value={filters.max_area} placeholder="40" onChange={set("max_area")} />
      <Select label="排序" value={filters.sort_by} options={SORT_OPTIONS} onChange={set("sort_by")} />

      <button
        onClick={() =>
          onChange({
            source: "",
            min_price: "",
            max_price: "",
            district: "",
            min_area: "",
            max_area: "",
            sort_by: "scraped_at_desc",
          })
        }
        className="text-sm text-gray-500 hover:text-gray-700 underline self-end pb-1.5"
      >
        清除篩選
      </button>
    </div>
  );
}
