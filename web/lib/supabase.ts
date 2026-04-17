import { createBrowserClient } from "@supabase/ssr";

// Client per a components del navegador (usa cookies, mai localStorage)
export const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
