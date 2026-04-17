"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth.store";

interface NavBarProps {
  title: string;
  onMenuToggle: () => void;
}

function UserAvatar({ displayName, email }: { displayName: string | null; email: string }) {
  const initials = displayName
    ? displayName
        .split(" ")
        .map((w) => w[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : email[0].toUpperCase();

  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-200 text-sm font-semibold text-blue-800 select-none">
      {initials}
    </span>
  );
}

export default function NavBar({ title, onMenuToggle }: NavBarProps) {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleLogout() {
    setDropdownOpen(false);
    await logout();
    router.replace("/login");
  }

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between px-4 py-3 bg-white border-b border-gray-100 shadow-sm">
      {/* Esquerra — hamburger */}
      <button
        aria-label="Obrir menú"
        onClick={onMenuToggle}
        className="flex flex-col gap-1.5 p-2 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <span className="block w-5 h-0.5 bg-gray-700" />
        <span className="block w-5 h-0.5 bg-gray-700" />
        <span className="block w-5 h-0.5 bg-gray-700" />
      </button>

      {/* Centre — títol */}
      <h1 className="text-base font-semibold text-gray-900">{title}</h1>

      {/* Dreta — avatar + dropdown */}
      <div className="relative" ref={dropdownRef}>
        <button
          aria-label="Menú de perfil"
          onClick={() => setDropdownOpen((o) => !o)}
          className="rounded-full hover:ring-2 hover:ring-blue-300 transition-all"
        >
          {user ? (
            <UserAvatar displayName={user.displayName} email={user.email} />
          ) : (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200 text-sm font-semibold text-gray-600">
              ?
            </span>
          )}
        </button>

        {dropdownOpen && (
          <div className="absolute right-0 mt-2 w-48 rounded-xl bg-white shadow-lg ring-1 ring-gray-100 py-1 z-40">
            <Link
              href="/profile"
              onClick={() => setDropdownOpen(false)}
              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <span>👤</span> Perfil
            </Link>
            <hr className="my-1 border-gray-100" />
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
            >
              <span>🚪</span> Tancar sessió
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
