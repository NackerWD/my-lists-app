/**
 * Tests directes per a l'auth store (logout, refreshToken, updateProfile, _initFromSession).
 * Supabase i el client API estan mockat completament.
 */

// ---- Mocks (s'han de definir ABANS dels imports per hoisting) ----

jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: jest.fn(), push: jest.fn() }),
}));

jest.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      setSession: jest.fn().mockResolvedValue({ data: {}, error: null }),
      signOut: jest.fn().mockResolvedValue({ error: null }),
      getSession: jest.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: jest
        .fn()
        .mockReturnValue({ data: { subscription: { unsubscribe: jest.fn() } } }),
    },
  },
}));

jest.mock("@/lib/api/client", () => ({
  post: jest.fn(),
  get: jest.fn(),
  patch: jest.fn(),
  del: jest.fn(),
}));

// ---- Imports ----
import { useAuthStore } from "@/lib/stores/auth.store";
import * as apiClient from "@/lib/api/client";
import { supabase } from "@/lib/supabase";

const mockPost = apiClient.post as jest.Mock;
const mockGet = apiClient.get as jest.Mock;
const mockPatch = apiClient.patch as jest.Mock;
const mockSetSession = supabase.auth.setSession as jest.Mock;
const mockSignOut = supabase.auth.signOut as jest.Mock;
const mockGetSession = supabase.auth.getSession as jest.Mock;

// ---- Setup ----

beforeEach(() => {
  jest.clearAllMocks();
  // Restableix getSession al default
  mockGetSession.mockResolvedValue({ data: { session: null } });
  useAuthStore.setState({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  });
});

// ---- Tests ----

describe("useAuthStore - logout", () => {
  it("fa logout correctament quan el backend respon", async () => {
    useAuthStore.setState({
      user: { id: "1", email: "u@test.com", displayName: null, avatarUrl: null },
      isAuthenticated: true,
    });
    mockPost.mockResolvedValueOnce({});

    await useAuthStore.getState().logout();

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/logout");
    expect(mockSignOut).toHaveBeenCalled();
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it("fa logout local fins i tot si el backend falla", async () => {
    mockPost.mockRejectedValueOnce(new Error("Network error"));

    await useAuthStore.getState().logout();

    expect(mockSignOut).toHaveBeenCalled();
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});

describe("useAuthStore - refreshToken", () => {
  it("no fa res si no hi ha sessió", async () => {
    mockGetSession.mockResolvedValueOnce({ data: { session: null } });

    await useAuthStore.getState().refreshToken();

    expect(mockPost).not.toHaveBeenCalled();
  });

  it("no fa res si no hi ha refresh_token a la sessió", async () => {
    mockGetSession.mockResolvedValueOnce({ data: { session: { refresh_token: null } } });

    await useAuthStore.getState().refreshToken();

    expect(mockPost).not.toHaveBeenCalled();
  });

  it("refresca el token correctament", async () => {
    mockGetSession.mockResolvedValueOnce({
      data: { session: { refresh_token: "old-refresh" } },
    });
    mockPost.mockResolvedValueOnce({
      access_token: "new-access",
      refresh_token: "new-refresh",
      token_type: "bearer",
      expires_in: 900,
    });

    await useAuthStore.getState().refreshToken();

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/refresh", {
      refresh_token: "old-refresh",
    });
    expect(mockSetSession).toHaveBeenCalledWith({
      access_token: "new-access",
      refresh_token: "new-refresh",
    });
  });

  it("fa signOut si el refresh falla", async () => {
    mockGetSession.mockResolvedValueOnce({
      data: { session: { refresh_token: "bad-refresh" } },
    });
    mockPost.mockRejectedValueOnce(new Error("Token expired"));

    await useAuthStore.getState().refreshToken();

    expect(mockSignOut).toHaveBeenCalled();
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});

describe("useAuthStore - updateProfile", () => {
  it("actualitza el perfil correctament", async () => {
    mockPatch.mockResolvedValueOnce({
      id: "1",
      email: "u@test.com",
      display_name: "Nou Nom",
      avatar_url: null,
      created_at: "2024-01-01T00:00:00Z",
    });

    await useAuthStore.getState().updateProfile({ displayName: "Nou Nom" });

    expect(mockPatch).toHaveBeenCalledWith("/api/v1/users/me", {
      display_name: "Nou Nom",
      avatar_url: undefined,
    });
    expect(useAuthStore.getState().user?.displayName).toBe("Nou Nom");
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it("guarda l'error i re-llança si la crida falla", async () => {
    mockPatch.mockRejectedValueOnce(new Error("Server error"));

    await expect(
      useAuthStore.getState().updateProfile({ displayName: "Fail" })
    ).rejects.toThrow("Server error");

    expect(useAuthStore.getState().error).toBe("Server error");
    expect(useAuthStore.getState().isLoading).toBe(false);
  });
});

describe("useAuthStore - _initFromSession", () => {
  it("no fa res si no hi ha sessió", async () => {
    mockGetSession.mockResolvedValueOnce({ data: { session: null } });

    await useAuthStore.getState()._initFromSession();

    expect(mockGet).not.toHaveBeenCalled();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("carrega el perfil si hi ha sessió activa", async () => {
    mockGetSession.mockResolvedValueOnce({
      data: { session: { access_token: "tok", refresh_token: "ref" } },
    });
    mockGet.mockResolvedValueOnce({
      id: "1",
      email: "u@test.com",
      display_name: "Test",
      avatar_url: null,
      created_at: "2024-01-01T00:00:00Z",
    });

    await useAuthStore.getState()._initFromSession();

    expect(mockGet).toHaveBeenCalledWith("/api/v1/auth/me");
    expect(useAuthStore.getState().user?.email).toBe("u@test.com");
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it("reseta l'estat si la crida al perfil falla", async () => {
    mockGetSession.mockResolvedValueOnce({
      data: { session: { access_token: "tok", refresh_token: "ref" } },
    });
    mockGet.mockRejectedValueOnce(new Error("Unauthorized"));

    await useAuthStore.getState()._initFromSession();

    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});

describe("useAuthStore - clearError", () => {
  it("neteja l'error", () => {
    useAuthStore.setState({ error: "Un error" });
    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });
});

describe("useAuthStore - login error handling", () => {
  it("guarda l'error i re-llança si el login falla", async () => {
    mockPost.mockRejectedValueOnce(new Error("Credencials incorrectes"));

    await expect(
      useAuthStore.getState().login("u@test.com", "wrongpass")
    ).rejects.toThrow("Credencials incorrectes");

    expect(useAuthStore.getState().error).toBe("Credencials incorrectes");
    expect(useAuthStore.getState().isLoading).toBe(false);
  });
});

describe("useAuthStore - register error handling", () => {
  it("guarda l'error i re-llança si el registre falla", async () => {
    mockPost.mockRejectedValueOnce(new Error("Email ja registrat"));

    await expect(
      useAuthStore.getState().register("u@test.com", "password12345")
    ).rejects.toThrow("Email ja registrat");

    expect(useAuthStore.getState().error).toBe("Email ja registrat");
    expect(useAuthStore.getState().isLoading).toBe(false);
  });
});
