// Tipus TypeScript que reflecteixen els schemas del backend (Pydantic v2)

export interface ListResponse {
  id: string;
  owner_id: string;
  list_type_id: string | null;
  list_type_slug?: string | null;
  list_type_label?: string | null;
  title: string;
  description: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string | null;
  member_count: number;
  item_count: number;
}

export interface ListCreate {
  title: string;
  description?: string | null;
  list_type_id?: string | null;
}

export interface ListUpdate {
  title?: string | null;
  description?: string | null;
  is_archived?: boolean | null;
}

export interface ListItemResponse {
  id: string;
  list_id: string;
  created_by: string | null;
  content: string;
  is_checked: boolean;
  position: number;
  due_date: string | null;
  priority: "high" | "medium" | "low" | null;
  remind_at: string | null;
  reminded_at?: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string | null;
}

export interface ListItemCreate {
  content: string;
  due_date?: string | null;
  priority?: "high" | "medium" | "low" | null;
  remind_at?: string | null;
  metadata?: Record<string, unknown> | null;
  position?: number;
}

export interface ListItemUpdate {
  content?: string | null;
  is_checked?: boolean | null;
  position?: number | null;
  due_date?: string | null;
  priority?: "high" | "medium" | "low" | null;
  remind_at?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface MemberResponse {
  id: string;
  list_id: string;
  user_id: string;
  role: "owner" | "editor" | "viewer";
  joined_at: string;
  email: string;
  display_name: string | null;
}

export interface InvitationResponse {
  invitation_id: string;
  list_id: string;
  list_title: string | null;
  invited_by: string;
  email: string;
  role: "editor" | "viewer";
  status: "pending" | "accepted" | "expired";
  expires_at: string;
}

export interface InviteRequest {
  email: string;
  role: "editor" | "viewer";
}

export interface InviteLinkResponse {
  invitation_id: string;
  link: string;
}

export interface AcceptInvitationResponse {
  list_id: string;
  role: string;
}
