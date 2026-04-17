import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // En CI (GitHub Actions), output: 'export' es deshabilita per evitar errors
  // amb rutes dinàmiques stub. Per builds de Capacitor, cal definir
  // NEXT_OUTPUT_EXPORT=export a l'entorn local.
  ...(process.env.NEXT_OUTPUT_EXPORT === "export" ? { output: "export" } : {}),
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
