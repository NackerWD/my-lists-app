"use client";

export const dynamic = "force-dynamic";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import NavBar from "@/components/ui/NavBar";
import SideMenu from "@/components/ui/SideMenu";
import ItemRow from "@/components/items/ItemRow";
import InviteModal from "@/components/lists/InviteModal";
import PresenceIndicator from "@/components/lists/PresenceIndicator";
import { getList } from "@/lib/api/lists";
import { createItem, deleteItem, getItems, updateItem } from "@/lib/api/list-items";
import { getMembers, removeMember } from "@/lib/api/members";
import { useListSocket } from "@/lib/hooks/useListSocket";
import { supabase } from "@/lib/supabase";

export default function ListDetailPage() {
  const params = useParams();
  const router = useRouter();
  const listId = params.id as string;
  const queryClient = useQueryClient();
  const [menuOpen, setMenuOpen] = useState(false);
  const [newContent, setNewContent] = useState("");
  const [inviteOpen, setInviteOpen] = useState(false);
  const [showMembers, setShowMembers] = useState(false);

  const { connectedCount, isConnected } = useListSocket(listId);

  const {
    data: list,
    isLoading: listLoading,
    isError: listError,
  } = useQuery({
    queryKey: ["list", listId],
    queryFn: () => getList(listId),
    enabled: !!listId,
  });

  const { data: items, isLoading: itemsLoading } = useQuery({
    queryKey: ["items", listId],
    queryFn: () => getItems(listId),
    enabled: !!listId,
  });

  const { data: members } = useQuery({
    queryKey: ["members", listId],
    queryFn: () => getMembers(listId),
    enabled: showMembers && !!listId,
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

  const removeMemberMutation = useMutation({
    mutationFn: (userId: string) => removeMember(listId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", listId] });
    },
  });

  async function getCurrentUserId(): Promise<string | null> {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.user?.id ?? null;
  }

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

  async function handleRemoveMember(userId: string) {
    const currentUserId = await getCurrentUserId();
    if (userId === currentUserId) return;
    removeMemberMutation.mutate(userId);
  }

  const isLoading = listLoading || itemsLoading;
  const isOwner = list && members?.some((m) => m.role === "owner");

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <NavBar
        title={list?.title ?? "Llista"}
        onMenuToggle={() => setMenuOpen(true)}
      />
      <SideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />

      <main className="flex-1 p-4 max-w-2xl mx-auto w-full pb-24">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => router.push("/lists")}
            className="text-sm text-blue-600 hover:underline"
          >
            ← Totes les llistes
          </button>
          <div className="flex items-center gap-3">
            <PresenceIndicator connectedCount={connectedCount} isConnected={isConnected} />
            <button
              onClick={() => setShowMembers((v) => !v)}
              className="text-sm text-gray-500 hover:text-gray-800"
            >
              {list?.member_count ?? 0} membre{(list?.member_count ?? 0) !== 1 ? "s" : ""}
            </button>
            <button
              onClick={() => setInviteOpen(true)}
              className="px-3 py-1.5 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              + Convidar
            </button>
          </div>
        </div>

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

            {showMembers && members && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 mb-4">
                <div className="px-4 py-3 border-b border-gray-100">
                  <h2 className="text-sm font-semibold text-gray-700">Membres</h2>
                </div>
                <ul className="divide-y divide-gray-100">
                  {members.map((member) => (
                    <li key={member.id} className="flex items-center justify-between px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {member.display_name ?? member.email}
                        </p>
                        <p className="text-xs text-gray-400">{member.email}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5">
                          {member.role}
                        </span>
                        {isOwner && member.role !== "owner" && (
                          <button
                            onClick={() => handleRemoveMember(member.user_id)}
                            disabled={removeMemberMutation.isPending}
                            className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50"
                          >
                            Eliminar
                          </button>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
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

      <InviteModal
        listId={listId}
        isOpen={inviteOpen}
        onClose={() => setInviteOpen(false)}
      />
    </div>
  );
}
