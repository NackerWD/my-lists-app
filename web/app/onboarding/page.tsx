"use client";

export const dynamic = "force-static";

import { useState } from "react";

const STEPS = [
  {
    title: "Benvingut/da!",
    description: "Crea i comparteix llistes de qualsevol tipus amb les persones que estimes.",
  },
  {
    title: "Col·laboració en temps real",
    description: "Edita llistes simultàniament amb amics i família. Els canvis es veuen a l'instant.",
  },
  {
    title: "Funciona sense connexió",
    description: "Afegeix ítems sense internet. Es sincronitzaran automàticament quan torneu a estar en línia.",
  },
];

export default function OnboardingPage() {
  const [step, setStep] = useState(0);

  const isFirst = step === 0;
  const isLast = step === STEPS.length - 1;

  return (
    <main className="flex flex-col min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-sm text-center space-y-6">
        {/* Step indicators */}
        <div className="flex justify-center gap-2">
          {STEPS.map((_, i) => (
            <span
              key={i}
              className={`h-2 w-2 rounded-full transition-colors ${i === step ? "bg-blue-600" : "bg-gray-300"}`}
            />
          ))}
        </div>

        <div className="space-y-3 min-h-[120px] flex flex-col items-center justify-center">
          <h2 className="text-2xl font-bold">{STEPS[step].title}</h2>
          <p className="text-gray-600 text-sm leading-relaxed">{STEPS[step].description}</p>
        </div>

        <div className="flex gap-3">
          {!isFirst && (
            <button
              onClick={() => setStep((s) => s - 1)}
              className="flex-1 rounded-md border px-4 py-2 text-sm font-medium hover:bg-gray-50"
            >
              Enrere
            </button>
          )}
          <button
            onClick={() => {
              if (isLast) {
                // TODO: implementar — redirigir a /login o /home
                window.location.href = "/login";
              } else {
                setStep((s) => s + 1);
              }
            }}
            className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {isLast ? "Comença" : "Següent"}
          </button>
        </div>
      </div>
    </main>
  );
}
