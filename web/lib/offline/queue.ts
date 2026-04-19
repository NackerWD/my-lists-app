import { openDB, type DBSchema, type IDBPDatabase } from "idb";
import type { QueryClient } from "@tanstack/react-query";

import { getAuthHeaders } from "@/lib/api/session-headers";

const DB_NAME = "lists-offline-queue";
const STORE = "operations";
const DB_VERSION = 2;
const MAX_RETRIES = 3;
const BASE_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 30_000;

export type QueuedMethod = "POST" | "PATCH" | "DELETE";

export interface QueuedOperation {
  id: string;
  timestamp: number;
  method: QueuedMethod;
  url: string;
  body?: unknown;
  /** Claus TanStack Query a invalidar després d'èxit */
  queryKeys: string[][];
  retries: number;
  /** Epoch ms: no reprocessar abans d'aquest moment (backoff exponencial) */
  nextAttemptAt?: number;
}

interface OfflineQueueDB extends DBSchema {
  operations: {
    key: string;
    value: QueuedOperation;
    indexes: { by_timestamp: number };
  };
}

function inferQueryKeysFromUrl(url: string): string[][] {
  try {
    const u = new URL(url);
    const path = u.pathname;
    const listItems = path.match(/^\/api\/v1\/lists\/([^/]+)\/items(?:\/([^/]+))?$/);
    if (listItems) {
      const listId = listItems[1];
      const keys: string[][] = [["items", listId], ["lists"]];
      return keys;
    }
  } catch {
    /* URL relativa o invàlida */
  }
  return [];
}

async function getDB(): Promise<IDBPDatabase<OfflineQueueDB>> {
  return openDB<OfflineQueueDB>(DB_NAME, DB_VERSION, {
    upgrade(db, oldVersion) {
      if (oldVersion < 1) {
        const store = db.createObjectStore(STORE, { keyPath: "id" });
        store.createIndex("by_timestamp", "timestamp");
      }
    },
  });
}

export type EnqueueInput = Omit<QueuedOperation, "id" | "timestamp" | "retries" | "nextAttemptAt"> & {
  queryKeys?: string[][];
};

export async function enqueueOperation(input: EnqueueInput): Promise<void> {
  const db = await getDB();
  const queryKeys =
    input.queryKeys?.length ? input.queryKeys : inferQueryKeysFromUrl(input.url);
  const record: QueuedOperation = {
    ...input,
    queryKeys,
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    timestamp: Date.now(),
    retries: 0,
  };
  await db.put(STORE, record);
}

export async function getQueue(): Promise<QueuedOperation[]> {
  const db = await getDB();
  return db.getAllFromIndex(STORE, "by_timestamp");
}

export async function removeFromQueue(id: string): Promise<void> {
  const db = await getDB();
  await db.delete(STORE, id);
}

function backoffMs(retries: number): number {
  return Math.min(MAX_BACKOFF_MS, BASE_BACKOFF_MS * 2 ** retries);
}

async function invalidateKeys(
  queryClient: QueryClient,
  keys: string[][]
): Promise<void> {
  for (const key of keys) {
    await queryClient.invalidateQueries({ queryKey: key });
  }
}

/**
 * Processa la cua en ordre cronològic; reintents fins a MAX_RETRIES amb backoff exponencial.
 */
export async function processQueue(queryClient?: QueryClient): Promise<void> {
  const db = await getDB();
  const all = await db.getAllFromIndex(STORE, "by_timestamp");
  const now = Date.now();

  for (const op of all) {
    if (op.nextAttemptAt != null && op.nextAttemptAt > now) {
      continue;
    }

    try {
      const headers = await getAuthHeaders();
      const res = await fetch(op.url, {
        method: op.method,
        headers,
        body: op.body !== undefined ? JSON.stringify(op.body) : undefined,
      });

      if (res.ok) {
        await db.delete(STORE, op.id);
        const keys =
          op.queryKeys?.length ? op.queryKeys : inferQueryKeysFromUrl(op.url);
        if (queryClient) {
          await invalidateKeys(queryClient, keys);
        }
        continue;
      }

      const nextRetries = op.retries + 1;
      if (nextRetries > MAX_RETRIES) {
        await db.delete(STORE, op.id);
        continue;
      }
      await db.put(STORE, {
        ...op,
        retries: nextRetries,
        nextAttemptAt: Date.now() + backoffMs(nextRetries),
      });
    } catch {
      const nextRetries = op.retries + 1;
      if (nextRetries > MAX_RETRIES) {
        await db.delete(STORE, op.id);
        continue;
      }
      await db.put(STORE, {
        ...op,
        retries: nextRetries,
        nextAttemptAt: Date.now() + backoffMs(nextRetries),
      });
    }
  }
}

export async function clearQueue(): Promise<void> {
  const db = await getDB();
  await db.clear(STORE);
}
