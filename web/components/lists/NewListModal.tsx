"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createList } from "@/lib/api/lists";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function NewListModal({ isOpen, onClose }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [titleError, setTitleError] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => createList({ title: title.trim(), description: description.trim() || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lists"] });
      setTitle("");
      setDescription("");
      setTitleError("");
      onClose();
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setTitleError("El títol és obligatori");
      return;
    }
    setTitleError("");
    mutation.mutate();
  }

  function handleClose() {
    setTitle("");
    setDescription("");
    setTitleError("");
    mutation.reset();
    onClose();
  }

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="new-list-title"
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <h2 id="new-list-title" className="text-lg font-semibold text-gray-900 mb-4">
          Nova llista
        </h2>

        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-4">
            <label
              htmlFor="list-title"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Títol <span className="text-red-500">*</span>
            </label>
            <input
              id="list-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Llista de la compra"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            {titleError && (
              <p className="mt-1 text-xs text-red-600" role="alert">
                {titleError}
              </p>
            )}
          </div>

          <div className="mb-6">
            <label
              htmlFor="list-description"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Descripció
            </label>
            <textarea
              id="list-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Opcional"
              rows={2}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          {mutation.isError && (
            <p className="mb-4 text-xs text-red-600" role="alert">
              Error en crear la llista. Torna-ho a provar.
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
              disabled={mutation.isPending}
              className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {mutation.isPending ? "Creant…" : "Crear"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
