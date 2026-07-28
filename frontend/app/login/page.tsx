import Link from "next/link";
import { Building2 } from "lucide-react";

import { LoginForm } from "@/components/auth/login-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="gradient-auth relative hidden flex-col justify-between p-10 text-white lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
            <Building2 className="h-6 w-6" />
          </div>
          <div>
            <p className="text-lg font-bold">Gestion Immobilière</p>
            <p className="text-sm text-white/70">Votre espace professionnel</p>
          </div>
        </div>
        <div>
          <h1 className="text-4xl font-bold leading-tight">
            Gérez vos biens,<br />vos locataires,<br />en toute sérénité.
          </h1>
          <p className="mt-4 max-w-md text-white/75">
            Tableaux de bord, paiements, documents et portails locataire — tout est
            centralisé dans une interface claire et moderne.
          </p>
        </div>
        <p className="text-sm text-white/50">© Gestion Immobilière</p>
      </div>

      <div className="flex flex-col items-center justify-center px-4 py-10 pb-safe sm:px-6 sm:py-12">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
                <Building2 className="h-5 w-5" />
              </div>
              <p className="text-xl font-bold">Gestion Immobilière</p>
            </div>
          </div>

          <Card className="border-border/60 shadow-[var(--shadow-lg)]">
            <CardHeader>
              <CardTitle>Connexion</CardTitle>
              <CardDescription>Accédez à votre espace de gestion</CardDescription>
            </CardHeader>
            <CardContent>
              <LoginForm />
            </CardContent>
          </Card>

          <Button asChild variant="ghost" className="mt-6 w-full">
            <Link href="/">← Retour à l&apos;accueil</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
