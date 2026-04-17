"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth.store";

export default function RegisterPage() {
  const { register, isLoading, error, clearError } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (password.length < 12) {
      setLocalError("La contrasenya ha de tenir almenys 12 caràcters");
      return;
    }
    if (password !== confirm) {
      setLocalError("Les contrasenyes no coincideixen");
      return;
    }

    try {
      const message = await register(email, password);
      setSuccessMessage(message);
    } catch {
      // error ja és a l'store
    }
  }

  const displayError = localError ?? error;

  return (
    <main className="flex min-h-screen items-center justify-center p-4 bg-gray-50">
      <div className="w-full max-w-sm space-y-6 bg-white rounded-2xl shadow-sm p-8">
        <div className="space-y-1 text-center">
          <h1 className="text-2xl font-bold tracking-tight">Crea el teu compte</h1>
          <p className="text-sm text-gray-500">Comença a organitzar-te</p>
        </div>

        {successMessage ? (
          <div className="space-y-4">
            <div className="rounded-lg bg-green-50 border border-green-200 px-4 py-4 text-sm text-green-800 text-center">
              <p className="font-medium">✓ Compte creat</p>
              <p className="mt-1">{successMessage}</p>
            </div>
            <p className="text-center text-sm text-gray-600">
              <Link href="/login" className="font-medium text-blue-600 hover:underline">
                Ves a iniciar sessió
              </Link>
            </p>
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium mb-1">
                  Correu electrònic
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="tu@exemple.com"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium mb-1">
                  Contrasenya
                  <span className="text-gray-400 font-normal ml-1">(mínim 12 caràcters)</span>
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="••••••••••••"
                />
              </div>

              <div>
                <label htmlFor="confirm" className="block text-sm font-medium mb-1">
                  Confirma la contrasenya
                </label>
                <input
                  id="confirm"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Repeteix la contrasenya"
                />
              </div>

              {displayError && (
                <p role="alert" className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
                  {displayError}
                </p>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? "Creant compte..." : "Crea el compte"}
              </button>
            </form>

            <p className="text-center text-sm text-gray-600">
              Ja tens compte?{" "}
              <Link href="/login" className="font-medium text-blue-600 hover:underline">
                Inicia sessió
              </Link>
            </p>
          </>
        )}
      </div>
    </main>
  );
}
