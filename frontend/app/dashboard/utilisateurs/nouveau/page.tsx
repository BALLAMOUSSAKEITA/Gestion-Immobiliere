"use client";

import Link from "next/link";

import { SuperAdminRoute } from "@/components/auth/super-admin-route";
import { CreateUserForm } from "@/components/users/user-form";
import { Button } from "@/components/ui/button";

export default function NewUserPage() {
  return (
    <SuperAdminRoute>
      <div className="flex flex-col gap-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Nouvel utilisateur</h1>
            <p className="mt-2 text-muted-foreground">
              Créez un compte et assignez un rôle.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href="/dashboard/utilisateurs">Retour</Link>
          </Button>
        </div>
        <CreateUserForm />
      </div>
    </SuperAdminRoute>
  );
}
