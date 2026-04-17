"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { useAuthStore } from "@/lib/stores/auth.store";
import NavBar from "@/components/ui/NavBar";
import SideMenu from "@/components/ui/SideMenu";

export default function HomePage() {
  const router = useRouter();
  const { user, isAuthenticated, _initFromSession } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function init() {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.replace("/login");
        return;
      }

      if (!isAuthenticated) {
        await _initFromSession();
      }

      setChecking(false);
    }
    init();
  }, [isAuthenticated, router, _initFromSession]);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <NavBar title="Les meves llistes" onMenuToggle={() => setMenuOpen(true)} />

      <SideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />

      <main className="flex-1 p-4">
        <p className="text-gray-500 text-sm text-center mt-12">
          {user?.displayName
            ? `Hola, ${user.displayName}! Cap llista de moment.`
            : "Cap llista de moment. Crea\u2019n una!"}
        </p>
      </main>
    </div>
  );
}
