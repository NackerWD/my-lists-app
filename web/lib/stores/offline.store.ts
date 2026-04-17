import { create } from "zustand";
import { enqueueOperation, processQueue, type QueuedOperation } from "@/lib/offline/queue";

interface OfflineStore {
  isOnline: boolean;
  queueLength: number;
  setOnline: (online: boolean) => void;
  enqueue: (op: Omit<QueuedOperation, "id" | "timestamp" | "retries">) => Promise<void>;
  processQueue: () => Promise<void>;
}

export const useOfflineStore = create<OfflineStore>((set) => ({
  isOnline: typeof navigator !== "undefined" ? navigator.onLine : true,
  queueLength: 0,

  setOnline: (online: boolean) => {
    set({ isOnline: online });
    if (online) {
      processQueue().catch(console.error);
    }
  },

  enqueue: async (op) => {
    await enqueueOperation(op);
    set((s) => ({ queueLength: s.queueLength + 1 }));
  },

  processQueue: async () => {
    await processQueue();
    set({ queueLength: 0 });
  },
}));
