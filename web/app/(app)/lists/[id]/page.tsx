"use client";

export const dynamic = "force-dynamic";

export default function ListDetailPage({ params }: { params: { id: string } }) {
  // TODO: implementar — detall d'una llista i els seus ítems
  return (
    <main className="p-4">
      <h1 className="text-xl font-bold mb-4">Llista #{params.id}</h1>
      <p className="text-gray-500 text-sm">Carregant ítems…</p>
    </main>
  );
}
