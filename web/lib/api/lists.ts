import { del, get, patch, post } from "@/lib/api/client";
import type { ListCreate, ListResponse, ListUpdate } from "@/lib/types";

export const getLists = () => get<ListResponse[]>("/api/v1/lists/");

export const getList = (id: string) => get<ListResponse>(`/api/v1/lists/${id}`);

export const createList = (data: ListCreate) =>
  post<ListResponse>("/api/v1/lists/", data);

export const updateList = (id: string, data: ListUpdate) =>
  patch<ListResponse>(`/api/v1/lists/${id}`, data);

export const deleteList = (id: string) => del<void>(`/api/v1/lists/${id}`);
