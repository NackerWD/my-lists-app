"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import NavBar from "@/components/ui/NavBar";
import SideMenu from "@/components/ui/SideMenu";
import { getLists } from "@/lib/api/lists";
import { getItems } from "@/lib/api/list-items";
import type { ListItemResponse, ListResponse } from "@/lib/types";

const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;

function isUrgent(item: ListItemResponse): boolean {
  if (item.is_checked) return false;
  if (item.priority === "high") return true;
  if (item.due_date) {
    const diff = new Date(item.due_date).getTime() - Date.now();
    if (diff <= SEVEN_DAYS_MS) return true;
  }
  return false;
}

function sortUrgent(a: ListItemResponse, b: ListItemResponse): number {
  if (a.priority === "high" && b.priority !== "high") return -1;
  if (b.priority === "high" && a.priority !== "high") return 1;
  if (a.due_date && b.due_date)
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  if (a.due_date) return -1;
  if (b.due_date) return 1;
  return 0;
}

// Component per a una llista individual — pot cridar useQuery de forma vàlida
function ListGroupCard({
  list,
  onNavigate,
}: {
  list: ListResponse;
  onNavigate: () => void;
}) {
  const { data: items } = useQuery({
    queryKey: ["items", list.id],
    queryFn: () => getItems(list.id),
  });

  const urgent = (items ?? []).filter(isUrgent).sort(sortUrgent);
  if (urgent.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <button
        onClick={onNavigate}
        className="w-full flex items-center justify-between px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors"
      >
        <span className="font-semibold text-gray-800 text-sm truncate">
          {list.title}
        </span>
        <span className="text-xs text-blue-600 ml-2 shrink-0">Veure tot →</span>
      </button>
      <div className="divide-y divide-gray-100">
        {urgent.map((item) => (
          <div key={item.id} className="flex items-center gap-3 px-4 py-2.5">
            <span
              className={`h-4 w-4 rounded border-2 shrink-0 ${
                item.is_checked
                  ? "bg-blue-600 border-blue-600"
                  : "border-gray-300"
              }`}
            />
            <span
              className={`text-sm flex-1 truncate ${
                item.is_checked
                  ? "line-through text-gray-400"
                  : "text-gray-800"
              }`}
            >
              {item.content}
            </span>
            {item.priority === "high" && (
              <span className="text-xs bg-red-100 text-red-700 rounded-full px-2 py-0.5 shrink-0">
                Alta
              </span>
            )}
            {item.due_date && (
              <span className="text-xs text-gray-400 shrink-0">
                {new Date(item.due_date).toLocaleDateString("ca-ES", {
                  day: "numeric",
                  month: "short",
                })}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyState({ onNavigate }: { onNavigate: () => void }) {
  return (
    <div className="text-center py-12">
      <p className="text-2xl mb-2">✓</p>
      <p className="text-gray-600 font-medium mb-1">Tot al dia!</p>
      <p className="text-gray-400 text-sm mb-6">
        No hi ha ítems urgents ni amb venciment pròxim.
      </p>
      <button
        onClick={onNavigate}
        className="text-blue-600 text-sm font-medium hover:underline"
      >
        Veure totes les llistes →
      </button>
    </div>
  );
}

function SmartView({ lists }: { lists: ListResponse[] }) {
  const router = useRouter();

  if (lists.length === 0) {
    return <EmptyState onNavigate={() => router.push("/lists")} />;
  }

  return (
    <div className="grid gap-3">
      {lists.map((list) => (
        <ListGroupCard
          key={list.id}
          list={list}
          onNavigate={() => router.push(`/lists/${list.id}`)}
        />
      ))}
    </div>
  );
}

export default function HomePage() {
  const [menuOpen, setMenuOpen] = useState(false);

  const { data: lists, isLoading } = useQuery({
    queryKey: ["lists"],
    queryFn: getLists,
  });

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <NavBar title="Inici" onMenuToggle={() => setMenuOpen(true)} />
      <SideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />

      <main className="flex-1 p-4 max-w-2xl mx-auto w-full">
        <h1 className="text-xl font-bold text-gray-900 mb-4">Ítems urgents</h1>

        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          </div>
        )}

        {!isLoading && <SmartView lists={lists ?? []} />}
      </main>
    </div>
  );
}
