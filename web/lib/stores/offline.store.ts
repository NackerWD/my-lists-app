import { create } from "zustand";

import {
  enqueueOperation,
  processQueue as flushOfflineQueue,
  type EnqueueInput,
} from "@/lib/offline/queue";

interface OfflineStore {
  isOnline: boolean;
  queueLength: number;
  setOnline: (online: boolean) => void;
  enqueue: (op: EnqueueInput) => Promise<void>;
  /** Sense QueryClient no s'invaliden caches TanStack; prefer ``useOfflineQueue``. */
  processQueue: () => Promise<void>;
}

export const useOfflineStore = create<OfflineStore>((set) => ({
  isOnline: typeof navigator !== "undefined" ? navigator.onLine : true,
  queueLength: 0,

  setOnline: (online: boolean) => {
    set({ isOnline: online });
    if (online) {
      void flushOfflineQueue();
    }
  },

  enqueue: async (op) => {
    await enqueueOperation(op);
    set((s) => ({ queueLength: s.queueLength + 1 }));
  },

  processQueue: async () => {
    await flushOfflineQueue();
    set({ queueLength: 0 });
  },
}));
