"use client";

import { useState } from "react";
import type { ListItemResponse } from "@/lib/types";
import { ItemMetadataSummary } from "@/components/lists/ItemMetadataFields";

interface Props {
  item: ListItemResponse;
  listTypeSlug?: string;
  onToggle: (id: string, checked: boolean) => void;
  onDelete: (id: string) => void;
}

const PRIORITY_LABELS: Record<string, { label: string; class: string }> = {
  high: { label: "Alta", class: "bg-red-100 text-red-700" },
  medium: { label: "Mitjana", class: "bg-yellow-100 text-yellow-700" },
  low: { label: "Baixa", class: "bg-green-100 text-green-700" },
};

function formatDueDate(iso: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diff = date.getTime() - today.getTime();
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
  if (days < 0) return `Vencut fa ${Math.abs(days)}d`;
  if (days === 0) return "Avui";
  if (days === 1) return "Demà";
  return date.toLocaleDateString("ca-ES", { day: "numeric", month: "short" });
}

export default function ItemRow({ item, listTypeSlug = "todo", onToggle, onDelete }: Props) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const priority = item.priority ? PRIORITY_LABELS[item.priority] : null;
  const dueDateLabel = formatDueDate(item.due_date);
  const isOverdue =
    item.due_date && new Date(item.due_date) < new Date() && !item.is_checked;

  return (
    <div
      className={`flex items-center gap-3 py-3 px-1 border-b border-gray-100 last:border-0 group ${
        item.is_checked ? "opacity-60" : ""
      }`}
      data-testid="item-row"
    >
      <input
        type="checkbox"
        checked={item.is_checked}
        onChange={(e) => onToggle(item.id, e.target.checked)}
        className="h-5 w-5 rounded border-gray-300 text-blue-600 cursor-pointer shrink-0"
        aria-label={`Marca com a completat: ${item.content}`}
      />

      <span
        className={`flex-1 text-sm ${item.is_checked ? "line-through text-gray-400" : "text-gray-800"}`}
      >
        <span className="block">{item.content}</span>
        <ItemMetadataSummary listType={listTypeSlug} metadata={item.metadata} />
      </span>

      <div className="flex items-center gap-2 shrink-0">
        {priority && (
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${priority.class}`}
            data-testid="priority-badge"
          >
            {priority.label}
          </span>
        )}
        {dueDateLabel && (
          <span
            className={`text-xs ${isOverdue ? "text-red-600 font-medium" : "text-gray-400"}`}
          >
            {dueDateLabel}
          </span>
        )}
        {confirmDelete ? (
          <div className="flex gap-1">
            <button
              onClick={() => onDelete(item.id)}
              className="text-xs text-red-600 font-medium hover:underline"
            >
              Eliminar
            </button>
            <button
              onClick={() => setConfirmDelete(false)}
              className="text-xs text-gray-400 hover:underline"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmDelete(true)}
            className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-300 hover:text-red-500 text-lg leading-none"
            aria-label="Eliminar ítem"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
