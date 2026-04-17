import { createBrowserClient } from "@supabase/ssr";

// Usa valors placeholder si les variables no estan definides (ex: durant el build al CI).
// El client fallarà en les crides de xarxa, però no llança errors en inicialitzar-se.
export const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL ?? "https://placeholder.supabase.co",
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "placeholder-anon-key"
);
