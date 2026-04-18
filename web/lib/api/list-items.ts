import { del, get, patch, post } from "@/lib/api/client";
import type {
  ListItemCreate,
  ListItemResponse,
  ListItemUpdate,
} from "@/lib/types";

export const getItems = (listId: string) =>
  get<ListItemResponse[]>(`/api/v1/lists/${listId}/items`);

export const createItem = (listId: string, data: ListItemCreate) =>
  post<ListItemResponse>(`/api/v1/lists/${listId}/items`, data);

export const updateItem = (
  listId: string,
  itemId: string,
  data: ListItemUpdate
) => patch<ListItemResponse>(`/api/v1/lists/${listId}/items/${itemId}`, data);

export const deleteItem = (listId: string, itemId: string) =>
  del<void>(`/api/v1/lists/${listId}/items/${itemId}`);
