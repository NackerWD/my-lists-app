/** Shell estàtic per a `output: export` (Capacitor); les rutes reals es resolen al client. */
export async function generateStaticParams(): Promise<{ id: string }[]> {
  return [{ id: "__cap_placeholder__" }];
}

export default function ListIdLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
