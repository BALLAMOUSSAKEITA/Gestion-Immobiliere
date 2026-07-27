"use client";

import Link from "next/link";

import { LoginForm } from "@/components/auth/login-form";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col items-center justify-center gap-6 px-6 py-16">
      <div className="w-full text-center">
        <h1 className="text-2xl font-bold">Connexion</h1>
        <p className="mt-2 text-zinc-600">
          Connectez-vous pour accéder à votre espace.
        </p>
      </div>

      <LoginForm />

      <Button asChild variant="outline" className="w-full">
        <Link href="/">Retour à l&apos;accueil</Link>
      </Button>
    </main>
  );
}
