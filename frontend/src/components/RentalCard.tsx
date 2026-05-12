import { Listing } from "@/types/listing";

const SOURCE_COLORS: Record<string, string> = {
  rental123: "bg-blue-100 text-blue-800",
  houseprice: "bg-green-100 text-green-800",
  tmm: "bg-purple-100 text-purple-800",
  ptt: "bg-orange-100 text-orange-800",
};

const SOURCE_LABELS: Record<string, string> = {
  rental123: "好租123",
  houseprice: "好房網",
  tmm: "崔媽媽",
  ptt: "PTT",
};

function CommuteTag({ minutes, label }: { minutes: number | null; label: string }) {
  if (minutes === null) {
    return (
      <span className="text-xs text-gray-400">{label}: —</span>
    );
  }

  const color =
    minutes <= 15
      ? "text-green-700 font-semibold"
      : minutes <= 30
      ? "text-yellow-700 font-semibold"
      : "text-red-600 font-semibold";

  return (
    <span className={`text-xs ${color}`}>
      {label}: {minutes}分
    </span>
  );
}

export default function RentalCard({ listing }: { listing: Listing }) {
  const sourceColor = SOURCE_COLORS[listing.source] || "bg-gray-100 text-gray-800";
  const sourceLabel = SOURCE_LABELS[listing.source] || listing.source;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex flex-col overflow-hidden">
      {/* Image placeholder */}
      <div className="h-36 bg-gray-100 relative overflow-hidden">
        {listing.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={listing.image_url}
            alt={listing.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 text-4xl">
            🏠
          </div>
        )}
        <span
          className={`absolute top-2 left-2 text-xs px-2 py-0.5 rounded-full font-medium ${sourceColor}`}
        >
          {sourceLabel}
        </span>
      </div>

      {/* Content */}
      <div className="p-3 flex flex-col gap-1.5 flex-1">
        {/* Title */}
        <h3 className="text-sm font-medium text-gray-900 line-clamp-2 leading-snug">
          {listing.title}
        </h3>

        {/* Price */}
        <p className="text-lg font-bold text-blue-600">
          {listing.price ? `NT$${listing.price.toLocaleString()}/月` : "價格洽談"}
        </p>

        {/* Meta row */}
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-gray-500">
          {listing.area_ping && <span>{listing.area_ping} 坪</span>}
          {listing.rooms && <span>{listing.rooms}</span>}
          {listing.floor && <span>{listing.floor}</span>}
        </div>

        {/* Address */}
        {(listing.district || listing.address) && (
          <p className="text-xs text-gray-500 truncate">
            📍 {listing.city}{listing.district} {listing.address || ""}
          </p>
        )}

        {/* Commute times */}
        <div className="mt-auto pt-2 border-t border-gray-100 flex gap-3">
          <CommuteTag minutes={listing.commute_min_guangbao} label="光寶" />
          <CommuteTag minutes={listing.commute_min_fengsan} label="鳳三" />
        </div>
      </div>

      {/* Link */}
      <a
        href={listing.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block text-center text-xs text-blue-500 hover:text-blue-700 py-2 border-t border-gray-100 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        查看原始物件 →
      </a>
    </div>
  );
}
