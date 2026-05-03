"use client";

interface ItemMetadataFieldsProps {
  listType: string;
  metadata: Record<string, unknown>;
  onChange: (metadata: Record<string, unknown>) => void;
  readOnly?: boolean;
}

export function ItemMetadataFields({
  listType,
  metadata,
  onChange,
  readOnly = false,
}: ItemMetadataFieldsProps) {
  if (listType === "shopping") {
    const qty =
      typeof metadata.quantity === "number" && !Number.isNaN(metadata.quantity)
        ? metadata.quantity
        : "";
    const unit = typeof metadata.unit === "string" ? metadata.unit : "";
    const price =
      typeof metadata.price === "number" && !Number.isNaN(metadata.price)
        ? metadata.price
        : "";

    return (
      <div className="flex flex-wrap gap-2 mt-1">
        <input
          type="number"
          placeholder="Quantitat"
          value={qty === "" ? "" : String(qty)}
          onChange={(e) => {
            const v = e.target.value;
            onChange({
              ...metadata,
              quantity: v === "" ? undefined : Number(v),
            });
          }}
          disabled={readOnly}
          className="w-20 text-sm border rounded px-2 py-1"
          min={1}
        />
        <input
          type="text"
          placeholder="Unitat (kg, unitats…)"
          value={unit}
          onChange={(e) => onChange({ ...metadata, unit: e.target.value })}
          disabled={readOnly}
          className="w-28 text-sm border rounded px-2 py-1"
        />
        <input
          type="number"
          placeholder="Preu"
          value={price === "" ? "" : String(price)}
          onChange={(e) => {
            const v = e.target.value;
            onChange({
              ...metadata,
              price: v === "" ? undefined : Number(v),
            });
          }}
          disabled={readOnly}
          className="w-24 text-sm border rounded px-2 py-1"
          step="0.01"
          min={0}
        />
      </div>
    );
  }

  if (listType === "wishlist") {
    const url = typeof metadata.url === "string" ? metadata.url : "";
    const price =
      typeof metadata.price === "number" && !Number.isNaN(metadata.price)
        ? metadata.price
        : "";

    return (
      <div className="flex flex-wrap gap-2 mt-1">
        <input
          type="url"
          placeholder="URL del producte"
          value={url}
          onChange={(e) => onChange({ ...metadata, url: e.target.value })}
          disabled={readOnly}
          className="flex-1 min-w-[120px] text-sm border rounded px-2 py-1"
        />
        <input
          type="number"
          placeholder="Preu"
          value={price === "" ? "" : String(price)}
          onChange={(e) => {
            const v = e.target.value;
            onChange({
              ...metadata,
              price: v === "" ? undefined : Number(v),
            });
          }}
          disabled={readOnly}
          className="w-24 text-sm border rounded px-2 py-1"
          step="0.01"
          min={0}
        />
      </div>
    );
  }

  return null;
}

interface ItemMetadataSummaryProps {
  listType: string;
  metadata: Record<string, unknown> | null | undefined;
}

export function ItemMetadataSummary({ listType, metadata }: ItemMetadataSummaryProps) {
  if (!metadata || typeof metadata !== "object") return null;

  if (listType === "shopping") {
    const parts: string[] = [];
    const q = metadata.quantity;
    const u = metadata.unit;
    if (typeof q === "number" && !Number.isNaN(q)) {
      parts.push(typeof u === "string" && u ? `${q} ${u}` : String(q));
    }
    const p = metadata.price;
    if (typeof p === "number" && !Number.isNaN(p)) parts.push(`${p}€`);
    return parts.length > 0 ? (
      <span className="text-xs text-gray-500 block mt-0.5">{parts.join(" · ")}</span>
    ) : null;
  }

  if (listType === "wishlist") {
    const url = metadata.url;
    const price = metadata.price;
    return (
      <div className="flex flex-wrap gap-2 items-center mt-0.5">
        {typeof url === "string" && url ? (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-500 underline"
          >
            Enllaç
          </a>
        ) : null}
        {typeof price === "number" && !Number.isNaN(price) ? (
          <span className="text-xs text-gray-500">{price}€</span>
        ) : null}
      </div>
    );
  }

  return null;
}
