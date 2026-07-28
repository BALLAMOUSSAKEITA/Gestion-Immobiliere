import Link from "next/link";
import { Home } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="gradient-hero flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <p className="text-8xl font-bold text-primary/20">404</p>
      <h1 className="mt-2 text-2xl font-bold text-foreground">Page introuvable</h1>
      <p className="mt-2 max-w-md text-muted-foreground">
        La page demandée n&apos;existe pas ou a été déplacée.
      </p>
      <Button asChild className="mt-6" variant="accent">
        <Link href="/">
          <Home className="mr-2 h-4 w-4" />
          Retour à l&apos;accueil
        </Link>
      </Button>
    </main>
  );
}
