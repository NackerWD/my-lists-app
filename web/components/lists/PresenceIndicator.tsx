"use client";

interface Props {
  connectedCount: number;
  isConnected: boolean;
}

const MAX_DOTS = 3;

export default function PresenceIndicator({ connectedCount, isConnected }: Props) {
  if (!isConnected && connectedCount === 0) return null;

  const dotsToShow = Math.min(connectedCount, MAX_DOTS);
  const overflow = connectedCount > MAX_DOTS ? connectedCount - MAX_DOTS : 0;

  return (
    <div className="flex items-center gap-1.5" title={`${connectedCount} usuari${connectedCount !== 1 ? "s" : ""} en línia`}>
      {Array.from({ length: dotsToShow }).map((_, i) => (
        <span
          key={i}
          className="h-2.5 w-2.5 rounded-full bg-green-500 animate-pulse"
          aria-hidden="true"
        />
      ))}
      {overflow > 0 && (
        <span className="text-xs text-gray-500 font-medium">+{overflow}</span>
      )}
      {connectedCount === 0 && isConnected && (
        <span className="h-2.5 w-2.5 rounded-full bg-gray-300" aria-hidden="true" />
      )}
    </div>
  );
}
