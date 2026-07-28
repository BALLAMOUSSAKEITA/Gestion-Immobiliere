"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchTenantDashboard,
  formatCurrency,
  type TenantPortalDashboard,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function TenantSpacePage() {
  const [dashboard, setDashboard] = useState<TenantPortalDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchTenantDashboard(token)
      .then(setDashboard)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <main className="flex flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Espace locataire</h1>
        <p className="mt-2 text-muted-foreground">
          Bienvenue{dashboard ? `, ${dashboard.tenant.full_name}` : ""}.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {dashboard && (
        <>
          {!dashboard.has_active_lease ? (
            <p className="rounded-xl border border-border bg-card shadow-sm p-4 text-muted-foreground">
              Aucun bail actif associé à votre compte.
            </p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-border bg-card shadow-sm p-4">
                <p className="text-sm text-muted-foreground">Logement</p>
                <p className="mt-1 text-xl font-bold">{dashboard.unit?.code}</p>
                <p className="text-sm text-muted-foreground">{dashboard.unit?.type}</p>
              </div>
              <div className="rounded-xl border border-border bg-card shadow-sm p-4">
                <p className="text-sm text-muted-foreground">Loyer mensuel</p>
                <p className="mt-1 text-xl font-bold">
                  {dashboard.lease ? formatCurrency(dashboard.lease.rent_amount) : "—"}
                </p>
              </div>
              <div className="rounded-xl border border-border bg-card shadow-sm p-4">
                <p className="text-sm text-muted-foreground">Mois en cours</p>
                <p
                  className={`mt-1 text-xl font-bold ${
                    dashboard.payment_status.current_month_paid
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {dashboard.payment_status.current_month_paid ? "Payé" : "Non payé"}
                </p>
              </div>
              <div className="rounded-xl border border-border bg-card shadow-sm p-4">
                <p className="text-sm text-muted-foreground">Total impayé</p>
                <p className="mt-1 text-xl font-bold text-red-600">
                  {formatCurrency(dashboard.payment_status.total_unpaid)}
                </p>
              </div>
              <div className="rounded-xl border border-border bg-card shadow-sm p-4">
                <p className="text-sm text-muted-foreground">Avis non lus</p>
                <p className="mt-1 text-xl font-bold">{dashboard.unread_notices}</p>
              </div>
              <div className="rounded-xl border border-border bg-card shadow-sm p-4">
                <p className="text-sm text-muted-foreground">Réparations actives</p>
                <p className="mt-1 text-xl font-bold">{dashboard.active_repairs}</p>
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <Button asChild>
              <Link href="/espace-locataire/mon-logement">Mon logement</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/espace-locataire/paiements">Paiements</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/espace-locataire/messages">Messages</Link>
            </Button>
          </div>
        </>
      )}
    </main>
  );
}
