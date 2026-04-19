"use client";

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";

const WS_BASE =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    .replace("https://", "wss://")
    .replace("http://", "ws://");

interface ListEvent {
  type: string;
  list_id: string;
  payload?: unknown;
}

interface UseListSocketReturn {
  connectedCount: number;
  isConnected: boolean;
}

export function useListSocket(listId: string): UseListSocketReturn {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const queryClient = useQueryClient();
  const [connectedCount, setConnectedCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const unmounted = useRef(false);
  // Store connect fn in a ref so onclose can call it without a circular dep
  const connectFn = useRef<() => Promise<void>>(async () => { /* initialised in useEffect */ });

  useEffect(() => {
    unmounted.current = false;

    connectFn.current = async () => {
      if (unmounted.current) return;
      if (ws.current?.readyState === WebSocket.OPEN) return;

      const {
        data: { session },
      } = await supabase.auth.getSession();

      const token = session?.access_token ?? "";
      const url = `${WS_BASE}/ws/lists/${listId}?token=${encodeURIComponent(token)}`;
      const socket = new WebSocket(url);
      ws.current = socket;

      socket.onopen = () => {
        if (unmounted.current) {
          socket.close();
          return;
        }
        setIsConnected(true);
      };

      socket.onmessage = (event) => {
        let data: ListEvent;
        try {
          data = JSON.parse(event.data as string) as ListEvent;
        } catch {
          return;
        }

        switch (data.type) {
          case "item_created":
          case "item_updated":
          case "item_deleted":
            queryClient.invalidateQueries({ queryKey: ["items", listId] });
            queryClient.invalidateQueries({ queryKey: ["lists"] });
            break;
          case "list_updated":
            queryClient.invalidateQueries({ queryKey: ["lists"] });
            queryClient.invalidateQueries({ queryKey: ["list", listId] });
            break;
          case "list_deleted":
            queryClient.invalidateQueries({ queryKey: ["lists"] });
            break;
          case "user_connected":
            setConnectedCount((n) => n + 1);
            break;
          case "user_disconnected":
            setConnectedCount((n) => Math.max(0, n - 1));
            break;
          default:
            break;
        }
      };

      socket.onerror = () => {
        socket.close();
      };

      socket.onclose = () => {
        setIsConnected(false);
        if (!unmounted.current) {
          reconnectTimer.current = setTimeout(() => {
            void connectFn.current?.();
          }, 3000);
        }
      };
    };

    void connectFn.current();

    return () => {
      unmounted.current = true;
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
      ws.current?.close();
    };
  }, [listId, queryClient]);

  return { connectedCount, isConnected };
}
