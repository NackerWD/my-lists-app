"use client";

import { useNetworkStatus } from "@/lib/hooks/useNetworkStatus";

export function OfflineBanner() {
  const { isOnline } = useNetworkStatus();
  if (isOnline) return null;
  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-amber-500 text-white text-center py-2 text-sm font-medium">
      Sense connexió — els canvis es sincronitzaran en reconnectar
    </div>
  );
}
