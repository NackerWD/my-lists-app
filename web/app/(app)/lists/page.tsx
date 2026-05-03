"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import NavBar from "@/components/ui/NavBar";
import SideMenu from "@/components/ui/SideMenu";
import ListCard from "@/components/lists/ListCard";
import NewListModal from "@/components/lists/NewListModal";
import { getLists } from "@/lib/api/lists";

export default function ListsPage() {
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const { data: lists, isLoading, isError } = useQuery({
    queryKey: ["lists"],
    queryFn: getLists,
  });

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <NavBar title="Les meves llistes" onMenuToggle={() => setMenuOpen(true)} />
      <SideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />

      <main className="flex-1 p-4 max-w-2xl mx-auto w-full">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-gray-900">Llistes</h1>
          <button
            onClick={() => setModalOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 transition-colors"
          >
            + Nova llista
          </button>
        </div>

        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          </div>
        )}

        {isError && (
          <p className="text-center text-red-500 text-sm py-8">
            Error en carregar les llistes. Torna-ho a provar.
          </p>
        )}

        {lists && lists.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400 text-sm mb-4">
              Encara no tens cap llista.
            </p>
            <button
              onClick={() => setModalOpen(true)}
              className="text-blue-600 text-sm font-medium hover:underline"
            >
              Crea la primera llista
            </button>
          </div>
        )}

        {lists && lists.length > 0 && (
          <div className="grid gap-3">
            {lists.map((list) => (
              <ListCard
                key={list.id}
                list={list}
                onClick={() => router.push(`/lists/${list.id}`)}
              />
            ))}
          </div>
        )}
      </main>

      <NewListModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
