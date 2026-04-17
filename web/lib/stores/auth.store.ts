import { create } from "zustand";
import { supabase } from "@/lib/supabase";
import { get, patch, post } from "@/lib/api/client";

interface User {
  id: string;
  email: string;
  displayName: string | null;
  avatarUrl: string | null;
}

interface UserProfileResponse {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<string>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  updateProfile: (data: { displayName?: string; avatarUrl?: string }) => Promise<void>;
  clearError: () => void;
  _initFromSession: () => Promise<void>;
}

function mapProfile(p: UserProfileResponse): User {
  return {
    id: p.id,
    email: p.email,
    displayName: p.display_name,
    avatarUrl: p.avatar_url,
  };
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  clearError: () => set({ error: null }),

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await post<TokenResponse>("/api/v1/auth/login", { email, password });

      // Sincronitza la sessió amb el client Supabase (escriu cookies per al middleware)
      await supabase.auth.setSession({
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
      });

      const profile = await get<UserProfileResponse>("/api/v1/auth/me");
      set({ user: mapProfile(profile), isAuthenticated: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error en iniciar sessió";
      set({ error: message });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await post<{ message: string }>("/api/v1/auth/register", { email, password });
      return data.message;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error en registrar el compte";
      set({ error: message });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await post("/api/v1/auth/logout");
    } catch {
      // Continuem amb el logout local encara que el backend falli
    } finally {
      await supabase.auth.signOut();
      set({ user: null, isAuthenticated: false, isLoading: false, error: null });
    }
  },

  refreshToken: async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.refresh_token) return;

    try {
      const tokens = await post<TokenResponse>("/api/v1/auth/refresh", {
        refresh_token: session.refresh_token,
      });
      await supabase.auth.setSession({
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
      });
    } catch {
      await supabase.auth.signOut();
      set({ user: null, isAuthenticated: false });
    }
  },

  updateProfile: async ({ displayName, avatarUrl }) => {
    set({ isLoading: true, error: null });
    try {
      const profile = await patch<UserProfileResponse>("/api/v1/users/me", {
        display_name: displayName,
        avatar_url: avatarUrl,
      });
      set({ user: mapProfile(profile) });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error en actualitzar el perfil";
      set({ error: message });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  _initFromSession: async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) return;

    try {
      const profile = await get<UserProfileResponse>("/api/v1/auth/me");
      set({ user: mapProfile(profile), isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    }
  },
}));

// Sincronitza l'estat de Zustand quan Supabase canvia de sessió
supabase.auth.onAuthStateChange(async (event, session) => {
  if (event === "SIGNED_OUT" || !session) {
    useAuthStore.setState({ user: null, isAuthenticated: false });
  }
  if (event === "TOKEN_REFRESHED" && session) {
    // Els nous tokens ja estan al client Supabase; re-fetch del perfil no cal
  }
});
