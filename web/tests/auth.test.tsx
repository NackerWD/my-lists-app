/**
 * Tests del flux d'autenticació: formularis de login/register i component NavBar.
 * Supabase i el client API estan mockat.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---- Mocks globals ----

jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: jest.fn(), push: jest.fn() }),
}));

jest.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      getSession: jest.fn().mockResolvedValue({ data: { session: null } }),
      setSession: jest.fn().mockResolvedValue({ data: {}, error: null }),
      signOut: jest.fn().mockResolvedValue({ error: null }),
      onAuthStateChange: jest.fn().mockReturnValue({ data: { subscription: { unsubscribe: jest.fn() } } }),
    },
  },
}));

jest.mock("@/lib/api/client", () => ({
  post: jest.fn(),
  get: jest.fn(),
  patch: jest.fn(),
  del: jest.fn(),
}));

// ---- Helpers ----
import * as apiClient from "@/lib/api/client";
const mockPost = apiClient.post as jest.Mock;
const mockGet = apiClient.get as jest.Mock;

import { useAuthStore } from "@/lib/stores/auth.store";

// Reset mocks i store entre tests
beforeEach(() => {
  jest.clearAllMocks();
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, error: null });
});

// ---- LoginPage ----
import LoginPage from "@/app/(auth)/login/page";

describe("LoginPage", () => {
  it("renderitza correctament els camps i el botó", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/correu electrònic/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contrasenya/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /inicia sessió/i })).toBeInTheDocument();
  });

  it("mostra l'enllaç de registre", () => {
    render(<LoginPage />);
    expect(screen.getByRole("link", { name: /registra't/i })).toBeInTheDocument();
  });

  it("crida login amb les credencials quan es fa submit", async () => {
    mockPost.mockResolvedValueOnce({
      access_token: "tok",
      refresh_token: "ref",
      token_type: "bearer",
      expires_in: 900,
    });
    mockGet.mockResolvedValueOnce({
      id: "uuid-1",
      email: "user@test.com",
      display_name: null,
      avatar_url: null,
      created_at: new Date().toISOString(),
    });

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/correu electrònic/i), {
      target: { value: "user@test.com" },
    });
    fireEvent.change(screen.getByLabelText(/contrasenya/i), {
      target: { value: "password12345" },
    });
    fireEvent.click(screen.getByRole("button", { name: /inicia sessió/i }));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/login", {
        email: "user@test.com",
        password: "password12345",
      });
    });
  });

  it("mostra l'estat loading durant la crida", async () => {
    let resolveLogin!: (v: unknown) => void;
    mockPost.mockReturnValueOnce(new Promise((res) => { resolveLogin = res; }));

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/correu electrònic/i), {
      target: { value: "user@test.com" },
    });
    fireEvent.change(screen.getByLabelText(/contrasenya/i), {
      target: { value: "password12345" },
    });
    fireEvent.click(screen.getByRole("button", { name: /inicia sessió/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /carregant/i })).toBeInTheDocument();
    });

    resolveLogin({
      access_token: "tok",
      refresh_token: "ref",
      token_type: "bearer",
      expires_in: 900,
    });
  });

  it("mostra missatge d'error quan el login falla", async () => {
    mockPost.mockRejectedValueOnce(new Error("HTTP 401: credencials incorrectes"));

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/correu electrònic/i), {
      target: { value: "bad@test.com" },
    });
    fireEvent.change(screen.getByLabelText(/contrasenya/i), {
      target: { value: "wrongpassword1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /inicia sessió/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });
});

// ---- RegisterPage ----
import RegisterPage from "@/app/(auth)/register/page";

describe("RegisterPage", () => {
  it("renderitza correctament", () => {
    render(<RegisterPage />);
    expect(screen.getByLabelText(/correu electrònic/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^contrasenya/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirma/i)).toBeInTheDocument();
  });

  it("valida que les passwords coincideixen", async () => {
    render(<RegisterPage />);
    fireEvent.change(screen.getByLabelText(/correu electrònic/i), {
      target: { value: "user@test.com" },
    });
    fireEvent.change(screen.getByLabelText(/^contrasenya/i), {
      target: { value: "password12345" },
    });
    fireEvent.change(screen.getByLabelText(/confirma/i), {
      target: { value: "different1234" },
    });
    fireEvent.click(screen.getByRole("button", { name: /crea el compte/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/no coincideixen/i);
    });
  });

  it("valida longitud mínima de 12 caràcters", async () => {
    render(<RegisterPage />);
    fireEvent.change(screen.getByLabelText(/correu electrònic/i), {
      target: { value: "user@test.com" },
    });
    fireEvent.change(screen.getByLabelText(/^contrasenya/i), {
      target: { value: "short" },
    });
    fireEvent.change(screen.getByLabelText(/confirma/i), {
      target: { value: "short" },
    });
    fireEvent.click(screen.getByRole("button", { name: /crea el compte/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/12 caràcters/i);
    });
  });

  it("mostra missatge d'èxit després del registre", async () => {
    mockPost.mockResolvedValueOnce({ message: "Verifica el teu correu per activar el compte" });

    render(<RegisterPage />);
    fireEvent.change(screen.getByLabelText(/correu electrònic/i), {
      target: { value: "new@test.com" },
    });
    fireEvent.change(screen.getByLabelText(/^contrasenya/i), {
      target: { value: "password12345" },
    });
    fireEvent.change(screen.getByLabelText(/confirma/i), {
      target: { value: "password12345" },
    });
    fireEvent.click(screen.getByRole("button", { name: /crea el compte/i }));

    await waitFor(() => {
      expect(screen.getByText(/Verifica el teu correu/i)).toBeInTheDocument();
    });
  });
});

// ---- NavBar ----
import NavBar from "@/components/ui/NavBar";

describe("NavBar", () => {
  const mockLogout = jest.fn();

  beforeEach(() => {
    useAuthStore.setState({
      user: { id: "1", email: "user@test.com", displayName: "Anna Puig", avatarUrl: null },
      isAuthenticated: true,
      logout: mockLogout,
    });
  });

  it("mostra les inicials de l'usuari correctament", () => {
    render(<NavBar title="Test" onMenuToggle={jest.fn()} />);
    expect(screen.getByText("AP")).toBeInTheDocument();
  });

  it("mostra el títol de la pàgina", () => {
    render(<NavBar title="Les meves llistes" onMenuToggle={jest.fn()} />);
    expect(screen.getByText("Les meves llistes")).toBeInTheDocument();
  });

  it("crida onMenuToggle en fer clic al hamburger", () => {
    const handleMenuToggle = jest.fn();
    render(<NavBar title="Test" onMenuToggle={handleMenuToggle} />);
    fireEvent.click(screen.getByLabelText(/obrir menú/i));
    expect(handleMenuToggle).toHaveBeenCalledTimes(1);
  });

  it("mostra el dropdown en clicar l'avatar", async () => {
    render(<NavBar title="Test" onMenuToggle={jest.fn()} />);
    fireEvent.click(screen.getByLabelText(/menú de perfil/i));
    await waitFor(() => {
      expect(screen.getByText(/tancar sessió/i)).toBeInTheDocument();
    });
  });
});
