import Link from "next/link";
import { Home } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background px-6 text-center">
      <p className="text-[28px] font-bold text-foreground">404</p>
      <h1 className="mt-2 text-sm font-medium text-foreground">Page introuvable</h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        La page demandée n&apos;existe pas ou a été déplacée.
      </p>
      <Button asChild className="mt-8" variant="accent">
        <Link href="/">
          <Home className="mr-2 h-4 w-4" />
          Retour à l&apos;accueil
        </Link>
      </Button>
    </main>
  );
}
