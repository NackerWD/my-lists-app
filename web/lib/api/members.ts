import { del, get } from "@/lib/api/client";
import type { MemberResponse } from "@/lib/types";

export const getMembers = (listId: string) =>
  get<MemberResponse[]>(`/api/v1/lists/${listId}/members`);

export const removeMember = (listId: string, userId: string) =>
  del<{ deleted: boolean }>(`/api/v1/lists/${listId}/members/${userId}`);
