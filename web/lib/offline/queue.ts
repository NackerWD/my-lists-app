import { openDB, type DBSchema, type IDBPDatabase } from "idb";

export interface QueuedOperation {
  id: string;
  method: string;
  url: string;
  body?: unknown;
  timestamp: number;
  retries: number;
}

interface OfflineQueueDB extends DBSchema {
  operations: {
    key: string;
    value: QueuedOperation;
    indexes: { by_timestamp: number };
  };
}

const DB_NAME = "lists-offline-queue";
const STORE = "operations";

async function getDB(): Promise<IDBPDatabase<OfflineQueueDB>> {
  return openDB<OfflineQueueDB>(DB_NAME, 1, {
    upgrade(db) {
      const store = db.createObjectStore(STORE, { keyPath: "id" });
      store.createIndex("by_timestamp", "timestamp");
    },
  });
}

export async function enqueueOperation(
  op: Omit<QueuedOperation, "id" | "timestamp" | "retries">
): Promise<void> {
  const db = await getDB();
  const record: QueuedOperation = {
    ...op,
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    timestamp: Date.now(),
    retries: 0,
  };
  await db.put(STORE, record);
}

export async function processQueue(): Promise<void> {
  const db = await getDB();
  const all = await db.getAllFromIndex(STORE, "by_timestamp");

  for (const op of all) {
    try {
      const res = await fetch(op.url, {
        method: op.method,
        headers: { "Content-Type": "application/json" },
        body: op.body !== undefined ? JSON.stringify(op.body) : undefined,
      });
      if (res.ok) {
        await db.delete(STORE, op.id);
      } else {
        await db.put(STORE, { ...op, retries: op.retries + 1 });
      }
    } catch {
      await db.put(STORE, { ...op, retries: op.retries + 1 });
    }
  }
}

export async function clearQueue(): Promise<void> {
  const db = await getDB();
  await db.clear(STORE);
}
