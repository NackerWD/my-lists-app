"use client";

import { useListTypes } from "@/lib/hooks/useListTypes";

const TYPE_ICONS: Record<string, string> = {
  todo: "📋",
  shopping: "🛒",
  tasks: "✅",
  wishlist: "❤️",
};

const TYPE_LABELS: Record<string, string> = {
  todo: "General",
  shopping: "Compres",
  tasks: "Tasques",
  wishlist: "Wishlist",
};

interface ListTypeSelectorProps {
  value: string;
  onChange: (typeId: string) => void;
}

export function ListTypeSelector({ value, onChange }: ListTypeSelectorProps) {
  const { data: types = [], isLoading } = useListTypes();

  if (isLoading) return <div className="text-sm text-gray-500">Carregant tipus…</div>;

  return (
    <div className="grid grid-cols-2 gap-2">
      {types.map((type) => (
        <button
          key={type.id}
          type="button"
          onClick={() => onChange(type.id)}
          className={`p-3 rounded-lg border-2 flex flex-col items-center gap-1 transition-colors
            ${
              value === type.id
                ? "border-blue-500 bg-blue-50 text-blue-700"
                : "border-gray-200 hover:border-gray-300"
            }`}
        >
          <span className="text-2xl">{TYPE_ICONS[type.slug] ?? "📋"}</span>
          <span className="text-sm font-medium">{TYPE_LABELS[type.slug] ?? type.label}</span>
        </button>
      ))}
    </div>
  );
}
