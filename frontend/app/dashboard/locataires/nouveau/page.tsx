"use client";

import { useRouter } from "next/navigation";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TenantForm } from "@/components/tenants/tenant-form";
import { AppHeader } from "@/components/layout/app-header";
import { ApiError, createTenant } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useState } from "react";

export default function NewTenantPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Nouveau locataire</h1>
          <p className="mt-2 text-zinc-600">Créer un dossier locataire complet.</p>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <TenantForm
          submitLabel="Créer le locataire"
          onSubmit={async (values) => {
            const token = getAccessToken();
            if (!token) return;
            try {
              const tenant = await createTenant(token, values);
              router.push(`/dashboard/locataires/${tenant.id}`);
            } catch (err) {
              setError(err instanceof ApiError ? err.message : "Création impossible");
              throw err;
            }
          }}
        />
      </main>
    </ProtectedRoute>
  );
}
