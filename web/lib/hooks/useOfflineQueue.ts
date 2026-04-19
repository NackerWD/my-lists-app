"use client";

import { useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useNetworkStatus } from "@/lib/hooks/useNetworkStatus";
import {
  enqueueOperation,
  processQueue,
  type EnqueueInput,
} from "@/lib/offline/queue";

/** Hook prim: escolta la xarxa i processa la cua IndexedDB (vegeu `lib/offline/queue.ts`). */
export function useOfflineQueue() {
  const queryClient = useQueryClient();
  const { isOnline } = useNetworkStatus();

  useEffect(() => {
    if (!isOnline) return;
    void processQueue(queryClient);
  }, [isOnline, queryClient]);

  const enqueue = useCallback((input: EnqueueInput) => enqueueOperation(input), []);

  const flush = useCallback(() => processQueue(queryClient), [queryClient]);

  return { isOnline, enqueue, processQueue: flush };
}
