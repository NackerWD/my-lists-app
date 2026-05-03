"use client";

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";

const WS_BASE =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    .replace("https://", "wss://")
    .replace("http://", "ws://");

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30000;
const RECONNECT_MAX_ATTEMPTS = 25;

function nextReconnectDelayMs(attempt: number): number {
  const exp = Math.min(
    RECONNECT_MAX_MS,
    RECONNECT_BASE_MS * 2 ** Math.max(0, attempt - 1),
  );
  const jitter = 0.85 + Math.random() * 0.3;
  return Math.min(RECONNECT_MAX_MS, Math.round(exp * jitter));
}

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
  const reconnectAttempt = useRef(0);
  const queryClient = useQueryClient();
  const [connectedCount, setConnectedCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const unmounted = useRef(false);
  const connectFn = useRef<() => Promise<void>>(async () => {
    /* initialised in useEffect */
  });

  useEffect(() => {
    unmounted.current = false;
    reconnectAttempt.current = 0;

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
        reconnectAttempt.current = 0;
        setIsConnected(true);
      };

      socket.onmessage = (event) => {
        let data: ListEvent;
        try {
          data = JSON.parse(event.data as string) as ListEvent;
        } catch {
          return;
        }

        if (data.type === "ping") {
          try {
            socket.send(JSON.stringify({ type: "pong" }));
          } catch {
            /* ignore */
          }
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
        if (unmounted.current) return;
        reconnectAttempt.current += 1;
        if (reconnectAttempt.current > RECONNECT_MAX_ATTEMPTS) {
          return;
        }
        const delay = nextReconnectDelayMs(reconnectAttempt.current);
        reconnectTimer.current = setTimeout(() => {
          void connectFn.current?.();
        }, delay);
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
