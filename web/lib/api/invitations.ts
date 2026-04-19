import { get, post } from "@/lib/api/client";
import type {
  AcceptInvitationResponse,
  InvitationResponse,
  InviteLinkResponse,
  InviteRequest,
} from "@/lib/types";

export const inviteMember = (listId: string, data: InviteRequest) =>
  post<InviteLinkResponse>(`/api/v1/lists/${listId}/invite`, data);

export const getInvitation = (token: string) =>
  get<InvitationResponse>(`/api/v1/invitations/${token}`);

export const acceptInvitation = (token: string) =>
  post<AcceptInvitationResponse>(`/api/v1/invitations/${token}/accept`);
