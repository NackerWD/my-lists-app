"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { acceptInvitation, getInvitation } from "@/lib/api/invitations";
import { supabase } from "@/lib/supabase";

export default function InvitePage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;
  const [isAuthed, setIsAuthed] = useState<boolean | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setIsAuthed(!!session);
    });
  }, []);

  const { data: invitation, isLoading, isError, error } = useQuery({
    queryKey: ["invitation", token],
    queryFn: () => getInvitation(token),
    enabled: !!token,
    retry: false,
  });

  const acceptMutation = useMutation({
    mutationFn: () => acceptInvitation(token),
    onSuccess: (data) => {
      router.push(`/lists/${data.list_id}`);
    },
  });

  function handleAccept() {
    if (!isAuthed) {
      router.push(`/login?next=/invite/${token}`);
      return;
    }
    acceptMutation.mutate();
  }

  const isExpired = isError && (error as Error)?.message?.includes("410");

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 w-full max-w-md p-8 text-center">
        {isLoading && (
          <div className="flex justify-center py-8">
            <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          </div>
        )}

        {isExpired && (
          <>
            <div className="text-4xl mb-4">⏰</div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">Invitació caducada</h1>
            <p className="text-sm text-gray-500 mb-6">
              Aquesta invitació ja no és vàlida. Demana una nova invitació al propietari de la llista.
            </p>
          </>
        )}

        {isError && !isExpired && (
          <>
            <div className="text-4xl mb-4">❌</div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">Invitació no trobada</h1>
            <p className="text-sm text-gray-500 mb-6">
              El link d&apos;invitació no és vàlid o ja ha estat usat.
            </p>
          </>
        )}

        {invitation && (
          <>
            <div className="text-4xl mb-4">📋</div>
            <h1 className="text-xl font-semibold text-gray-900 mb-1">
              T&apos;han convidat a una llista
            </h1>
            {invitation.list_title && (
              <p className="text-lg text-blue-600 font-medium mb-2">{invitation.list_title}</p>
            )}
            <p className="text-sm text-gray-500 mb-1">
              Rol: <span className="font-medium text-gray-700">{invitation.role === "editor" ? "Editor" : "Lector"}</span>
            </p>
            <p className="text-xs text-gray-400 mb-8">
              Caduca: {new Date(invitation.expires_at).toLocaleDateString("ca-ES")}
            </p>

            {acceptMutation.isError && (
              <p className="text-sm text-red-600 mb-4" role="alert">
                {(acceptMutation.error as Error)?.message?.includes("409")
                  ? "Ja ets membre d'aquesta llista."
                  : "Error en acceptar la invitació. Torna-ho a provar."}
              </p>
            )}

            <button
              onClick={handleAccept}
              disabled={acceptMutation.isPending}
              className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {acceptMutation.isPending
                ? "Processant…"
                : isAuthed === false
                ? "Inicia sessió per acceptar"
                : "Acceptar invitació"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
