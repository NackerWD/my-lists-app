"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { post } from "@/lib/api/client";

const INFO_STEPS = [
  {
    title: "Organitza la teva vida amb llistes",
    description:
      "Crea llistes de qualsevol tipus: tasques, compra, viatges, pel·lícules i molt més.",
  },
  {
    title: "Col·labora en temps real",
    description:
      "Comparteix llistes amb amics i família. Els canvis es veuen a l'instant per a tothom.",
  },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [listName, setListName] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const totalSteps = INFO_STEPS.length + 1;
  const isLastStep = step === totalSteps - 1;

  async function handleCreateList() {
    if (!listName.trim()) {
      router.push("/home");
      return;
    }
    setIsCreating(true);
    try {
      await post("/api/v1/lists", { title: listName.trim(), list_type_id: null });
    } catch {
      // stub — continua a home encara que falli
    } finally {
      setIsCreating(false);
      router.push("/home");
    }
  }

  return (
    <main className="flex flex-col min-h-screen items-center justify-center p-6 bg-gray-50">
      <div className="w-full max-w-sm space-y-8">
        {/* Indicadors de pas */}
        <div className="flex justify-center gap-2">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <span
              key={i}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === step ? "w-6 bg-blue-600" : "w-2 bg-gray-300"
              }`}
            />
          ))}
        </div>

        {isLastStep ? (
          <div className="space-y-6 text-center">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Crea la teva primera llista</h2>
              <p className="text-gray-600 text-sm">Posa-li un nom i comença ara mateix.</p>
            </div>
            <input
              type="text"
              value={listName}
              onChange={(e) => setListName(e.target.value)}
              placeholder="Ex: Llista de la compra"
              className="w-full rounded-lg border border-gray-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <div className="flex gap-3">
              <button
                onClick={() => router.push("/home")}
                className="flex-1 rounded-lg border border-gray-200 px-4 py-2.5 text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                Saltar
              </button>
              <button
                onClick={handleCreateList}
                disabled={isCreating}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isCreating ? "Creant..." : "Crear i començar"}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6 text-center">
            <div className="h-32 flex items-center justify-center">
              <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-4xl">{step === 0 ? "📋" : "👥"}</span>
              </div>
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">{INFO_STEPS[step].title}</h2>
              <p className="text-gray-600 text-sm leading-relaxed">{INFO_STEPS[step].description}</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => router.push("/home")}
                className="flex-1 rounded-lg border border-gray-200 px-4 py-2.5 text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                Saltar
              </button>
              <button
                onClick={() => setStep((s) => s + 1)}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
              >
                Continuar
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
