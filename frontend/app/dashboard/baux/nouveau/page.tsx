"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { LeaseForm } from "@/components/tenants/lease-form";
import { AppHeader } from "@/components/layout/app-header";
import {
  ApiError,
  createLease,
  fetchTenants,
  fetchUnits,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function NewLeasePage() {
  const router = useRouter();
  const [tenants, setTenants] = useState<{ id: string; label: string }[]>([]);
  const [units, setUnits] = useState<
    { id: string; label: string; rent_amount: string }[]
  >([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    Promise.all([
      fetchTenants(token, { page_size: 100, is_active: true }),
      fetchUnits(token, { status: "free", page_size: 100 }),
    ])
      .then(([tenantsData, unitsData]) => {
        setTenants(
          tenantsData.items.map((tenant) => ({
            id: tenant.id,
            label: `${tenant.first_name} ${tenant.last_name}`,
          })),
        );
        setUnits(
          unitsData.items.map((unit) => ({
            id: unit.id,
            label: `${unit.building_name ?? ""} — ${unit.code}`,
            rent_amount: unit.rent_amount,
          })),
        );
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Nouveau bail</h1>
          <p className="mt-2 text-muted-foreground">
            Attribuer un logement libre à un locataire.
          </p>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <LeaseForm
          tenants={tenants}
          units={units}
          onSubmit={async (values) => {
            const token = getAccessToken();
            if (!token) return;
            const lease = await createLease(token, values);
            router.push(`/dashboard/baux/${lease.id}`);
          }}
        />
      </main>
    </ProtectedRoute>
  );
}
