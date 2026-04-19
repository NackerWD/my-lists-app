"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { inviteMember } from "@/lib/api/invitations";

interface Props {
  listId: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function InviteModal({ listId, isOpen, onClose }: Props) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"editor" | "viewer">("editor");
  const [copied, setCopied] = useState(false);

  const mutation = useMutation({
    mutationFn: () => inviteMember(listId, { email: email.trim(), role }),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    mutation.mutate();
  }

  async function handleCopy() {
    if (!mutation.data?.link) return;
    await navigator.clipboard.writeText(mutation.data.link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleClose() {
    setEmail("");
    setRole("editor");
    setCopied(false);
    mutation.reset();
    onClose();
  }

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="invite-modal-title"
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <h2 id="invite-modal-title" className="text-lg font-semibold text-gray-900 mb-4">
          Convidar membre
        </h2>

        {mutation.isSuccess && mutation.data ? (
          <div>
            <p className="text-sm text-gray-600 mb-3">
              Invitació creada! Comparteix aquest link:
            </p>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                readOnly
                value={mutation.data.link}
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-xs text-gray-700 bg-gray-50 focus:outline-none"
              />
              <button
                onClick={handleCopy}
                className="px-3 py-2 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                {copied ? "Copiat!" : "Copiar"}
              </button>
            </div>
            <button
              onClick={handleClose}
              className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-200 rounded-lg"
            >
              Tancar
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate>
            <div className="mb-4">
              <label htmlFor="invite-email" className="block text-sm font-medium text-gray-700 mb-1">
                Correu electrònic
              </label>
              <input
                id="invite-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="membre@exemple.com"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
                required
              />
            </div>

            <div className="mb-6">
              <label htmlFor="invite-role" className="block text-sm font-medium text-gray-700 mb-1">
                Rol
              </label>
              <select
                id="invite-role"
                value={role}
                onChange={(e) => setRole(e.target.value as "editor" | "viewer")}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="editor">Editor — pot afegir i editar ítems</option>
                <option value="viewer">Lector — només pot veure la llista</option>
              </select>
            </div>

            {mutation.isError && (
              <p className="mb-4 text-xs text-red-600" role="alert">
                Error en crear la invitació. Torna-ho a provar.
              </p>
            )}

            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel·lar
              </button>
              <button
                type="submit"
                disabled={!email.trim() || mutation.isPending}
                className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {mutation.isPending ? "Enviant…" : "Convidar"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
