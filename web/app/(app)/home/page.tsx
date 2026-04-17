"use client";

export const dynamic = "force-dynamic";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth.store";

export default function HomePage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top nav */}
      <header className="flex items-center justify-between px-4 py-3 border-b">
        <button aria-label="Menú" className="p-2 rounded-md hover:bg-gray-100">
          <span className="block w-5 h-0.5 bg-gray-800 mb-1" />
          <span className="block w-5 h-0.5 bg-gray-800 mb-1" />
          <span className="block w-5 h-0.5 bg-gray-800" />
        </button>
        <h1 className="text-base font-semibold">Les meves llistes</h1>
        <button
          aria-label="Perfil"
          className="w-8 h-8 rounded-full bg-blue-200 flex items-center justify-center text-sm font-medium"
        >
          U
        </button>
      </header>

      {/* Main content */}
      <main className="flex-1 p-4">
        <p className="text-gray-500 text-sm text-center mt-8">
          {/* TODO: implementar — llistat de llistes de l'usuari */}
          Cap llista de moment. Crea&apos;n una!
        </p>
      </main>
    </div>
  );
}
