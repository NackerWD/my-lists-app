"use client";

export const dynamic = "force-dynamic";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import NavBar from "@/components/ui/NavBar";
import SideMenu from "@/components/ui/SideMenu";
import ItemRow from "@/components/items/ItemRow";
import { getList } from "@/lib/api/lists";
import { createItem, deleteItem, getItems, updateItem } from "@/lib/api/list-items";

export default function ListDetailPage() {
  const params = useParams();
  const router = useRouter();
  const listId = params.id as string;
  const queryClient = useQueryClient();
  const [menuOpen, setMenuOpen] = useState(false);
  const [newContent, setNewContent] = useState("");

  const {
    data: list,
    isLoading: listLoading,
    isError: listError,
  } = useQuery({
    queryKey: ["list", listId],
    queryFn: () => getList(listId),
    enabled: !!listId,
  });

  const {
    data: items,
    isLoading: itemsLoading,
  } = useQuery({
    queryKey: ["items", listId],
    queryFn: () => getItems(listId),
    enabled: !!listId,
  });

  const createMutation = useMutation({
    mutationFn: (content: string) => createItem(listId, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items", listId] });
      queryClient.invalidateQueries({ queryKey: ["lists"] });
      setNewContent("");
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, checked }: { id: string; checked: boolean }) =>
      updateItem(listId, id, { is_checked: checked }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items", listId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (itemId: string) => deleteItem(listId, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items", listId] });
      queryClient.invalidateQueries({ queryKey: ["lists"] });
    },
  });

  function handleAddItem(e: React.FormEvent) {
    e.preventDefault();
    const content = newContent.trim();
    if (!content) return;
    createMutation.mutate(content);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      const content = newContent.trim();
      if (!content) return;
      createMutation.mutate(content);
    }
  }

  const isLoading = listLoading || itemsLoading;

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <NavBar
        title={list?.title ?? "Llista"}
        onMenuToggle={() => setMenuOpen(true)}
      />
      <SideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />

      <main className="flex-1 p-4 max-w-2xl mx-auto w-full pb-24">
        <button
          onClick={() => router.push("/lists")}
          className="text-sm text-blue-600 hover:underline mb-4 inline-block"
        >
          ← Totes les llistes
        </button>

        {listError && (
          <p className="text-center text-red-500 text-sm py-8">
            Error en carregar la llista.
          </p>
        )}

        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          </div>
        )}

        {list && (
          <>
            {list.description && (
              <p className="text-sm text-gray-500 mb-4">{list.description}</p>
            )}

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 divide-y divide-gray-100 mb-4">
              {items && items.length === 0 && (
                <p className="text-center text-gray-400 text-sm py-8">
                  Sense ítems. Afegeix el primer a sota!
                </p>
              )}
              {items &&
                items.map((item) => (
                  <ItemRow
                    key={item.id}
                    item={item}
                    onToggle={(id, checked) =>
                      toggleMutation.mutate({ id, checked })
                    }
                    onDelete={(id) => deleteMutation.mutate(id)}
                  />
                ))}
            </div>
          </>
        )}
      </main>

      {/* Camp d'entrada fix al peu */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-lg">
        <form onSubmit={handleAddItem} className="max-w-2xl mx-auto flex gap-2">
          <input
            type="text"
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Afegir ítem nou…"
            className="flex-1 rounded-xl border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={!newContent.trim() || createMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 disabled:opacity-40"
          >
            Afegir
          </button>
        </form>
      </div>
    </div>
  );
}
