"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth.store";

interface SideMenuProps {
  open: boolean;
  onClose: () => void;
}

const NAV_ITEMS = [
  { href: "/home", label: "Inici", icon: "🏠" },
  { href: "/lists", label: "Llistes", icon: "📋" },
  { href: "/profile", label: "Perfil", icon: "👤" },
  { href: "/settings", label: "Configuració", icon: "⚙️" },
];

export default function SideMenu({ open, onClose }: SideMenuProps) {
  const router = useRouter();
  const { logout, user } = useAuthStore();

  // Tanca el menú amb Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (open) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // Evita scroll del body quan el menú és obert
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  async function handleLogout() {
    onClose();
    await logout();
    router.replace("/login");
  }

  return (
    <>
      {/* Overlay */}
      <div
        className={`fixed inset-0 z-40 bg-black/40 transition-opacity duration-300 ${
          open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside
        aria-label="Menú de navegació"
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-xl flex flex-col transition-transform duration-300 ease-in-out ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Capçalera */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <span className="font-bold text-lg text-gray-900">My Lists</span>
          <button
            aria-label="Tancar menú"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Usuari */}
        {user && (
          <div className="px-5 py-3 bg-gray-50 border-b border-gray-100">
            <p className="text-sm font-medium text-gray-900 truncate">
              {user.displayName ?? user.email}
            </p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
          </div>
        )}

        {/* Navegació */}
        <nav className="flex-1 py-3 overflow-y-auto">
          {NAV_ITEMS.map(({ href, label, icon }) => (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className="flex items-center gap-3 px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors"
            >
              <span className="text-lg">{icon}</span>
              {label}
            </Link>
          ))}
        </nav>

        {/* Peu — Tanca sessió */}
        <div className="border-t border-gray-100 p-3">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-5 py-3 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <span className="text-lg">🚪</span>
            Tanca sessió
          </button>
        </div>
      </aside>
    </>
  );
}
