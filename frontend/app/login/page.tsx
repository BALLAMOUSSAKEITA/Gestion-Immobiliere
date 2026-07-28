import Link from "next/link";
import { Building2 } from "lucide-react";

import { LoginForm } from "@/components/auth/login-form";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex h-16 items-center border-b border-border bg-card px-5 sm:px-10">
        <Link href="/" className="flex items-center gap-2">
          <Building2 className="h-7 w-7 text-accent" strokeWidth={2.5} />
          <span className="text-lg font-semibold text-accent">Gestion Immo</span>
        </Link>
      </header>

      <div className="flex flex-1 flex-col items-center justify-center px-4 py-12 pb-safe sm:px-6">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <h1 className="heading-section">Connexion</h1>
            <p className="mt-2 text-sm text-muted-foreground">Accédez à votre espace de gestion</p>
          </div>

          <div className="rounded-[12px] bg-card p-6 sm:p-8">
            <LoginForm />
          </div>

          <Button asChild variant="ghost" className="mt-6 w-full">
            <Link href="/">← Retour à l&apos;accueil</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
