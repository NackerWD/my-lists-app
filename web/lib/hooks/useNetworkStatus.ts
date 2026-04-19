"use client";

import { useState, useEffect } from "react";
import { Capacitor } from "@capacitor/core";
import { Network } from "@capacitor/network";

export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        if (Capacitor.isNativePlatform()) {
          const s = await Network.getStatus();
          if (!cancelled) setIsOnline(s.connected);
        } else if (typeof navigator !== "undefined") {
          if (!cancelled) setIsOnline(navigator.onLine);
        }
      } catch {
        if (!cancelled && typeof navigator !== "undefined") {
          setIsOnline(navigator.onLine);
        }
      }
    }
    void init();

    let removeNative: (() => void) | undefined;
    void Network.addListener("networkStatusChange", (s) => setIsOnline(s.connected))
      .then((h) => {
        removeNative = () => {
          void h.remove();
        };
      })
      .catch(() => {});

    const onOnline = () => setIsOnline(true);
    const onOffline = () => setIsOnline(false);
    if (typeof window !== "undefined") {
      window.addEventListener("online", onOnline);
      window.addEventListener("offline", onOffline);
    }

    return () => {
      cancelled = true;
      removeNative?.();
      if (typeof window !== "undefined") {
        window.removeEventListener("online", onOnline);
        window.removeEventListener("offline", onOffline);
      }
    };
  }, []);

  return { isOnline };
}
