import { create } from "zustand";
import { setAccessToken } from "@/lib/api/client";

interface User {
  id: string;
  email: string;
  displayName: string | null;
  avatarUrl: string | null;
}

interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,

  login: async (email: string, _password: string) => {
    // TODO: implementar — POST /api/v1/auth/login, guardar tokens, actualitzar estat
    void _password; // intentionally unused in mock
    const mockUser: User = {
      id: "00000000-0000-0000-0000-000000000000",
      email,
      displayName: null,
      avatarUrl: null,
    };
    setAccessToken("mock-access-token");
    set({ user: mockUser, isAuthenticated: true });
  },

  logout: () => {
    setAccessToken(null);
    set({ user: null, isAuthenticated: false });
  },

  refreshToken: async () => {
    // TODO: implementar — POST /api/v1/auth/refresh
  },
}));
