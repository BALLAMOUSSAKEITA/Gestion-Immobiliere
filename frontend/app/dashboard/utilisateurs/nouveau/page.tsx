"use client";

import Link from "next/link";

import { SuperAdminRoute } from "@/components/auth/super-admin-route";
import { AppHeader } from "@/components/layout/app-header";
import { CreateUserForm } from "@/components/users/user-form";
import { Button } from "@/components/ui/button";

export default function NewUserPage() {
  return (
    <SuperAdminRoute>
      <AppHeader />
      <main className="mx-auto w-full max-w-3xl px-6 py-10">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Nouvel utilisateur</h1>
            <p className="mt-2 text-zinc-600">
              Créez un compte et assignez un rôle.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href="/dashboard/utilisateurs">Retour</Link>
          </Button>
        </div>
        <CreateUserForm />
      </main>
    </SuperAdminRoute>
  );
}
