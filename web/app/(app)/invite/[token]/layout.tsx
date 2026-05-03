/** Shell estàtic per a `output: export` (Capacitor); els tokens reals es resolen al client. */
export async function generateStaticParams(): Promise<{ token: string }[]> {
  return [{ token: "__cap_placeholder__" }];
}

export default function InviteTokenLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
