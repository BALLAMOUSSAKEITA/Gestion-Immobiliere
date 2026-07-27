import { PublicHeader } from "@/components/layout/public-header";

export default function AnnoncesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <PublicHeader />
      {children}
    </>
  );
}
