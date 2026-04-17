"use client";

import type { ListResponse } from "@/lib/types";

interface Props {
  list: ListResponse;
  onClick: () => void;
}

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-green-100 text-green-700",
};

function formatRelativeDate(iso: string | null): string {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  if (days === 0) return "Avui";
  if (days === 1) return "Ahir";
  if (days < 7) return `Fa ${days} dies`;
  return new Date(iso).toLocaleDateString("ca-ES", {
    day: "numeric",
    month: "short",
  });
}

export default function ListCard({ list, onClick }: Props) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white rounded-2xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow focus:outline-none focus:ring-2 focus:ring-blue-500"
      aria-label={`Obrir llista ${list.title}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900 truncate">{list.title}</h3>
        {list.is_archived && (
          <span className="shrink-0 text-xs bg-gray-100 text-gray-500 rounded-full px-2 py-0.5">
            Arxivada
          </span>
        )}
      </div>

      {list.description && (
        <p className="mt-1 text-sm text-gray-500 line-clamp-2">
          {list.description}
        </p>
      )}

      <div className="mt-3 flex items-center gap-3 text-xs text-gray-400">
        <span>
          <span className="font-medium text-gray-700">{list.item_count}</span>{" "}
          {list.item_count === 1 ? "ítem" : "ítems"}
        </span>
        <span>·</span>
        <span>
          <span className="font-medium text-gray-700">{list.member_count}</span>{" "}
          {list.member_count === 1 ? "membre" : "membres"}
        </span>
        {list.updated_at && (
          <>
            <span>·</span>
            <span>{formatRelativeDate(list.updated_at)}</span>
          </>
        )}
      </div>
    </button>
  );
}

export { PRIORITY_COLORS };
