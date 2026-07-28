"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { DocumentLibrary } from "@/components/documents/document-library";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  createTenantAccount,
  fetchTenant,
  formatCurrency,
  ID_DOCUMENT_LABELS,
  PAYMENT_METHOD_LABELS,
  type TenantDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

export default function TenantDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const [tenant, setTenant] = useState<TenantDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [accountEmail, setAccountEmail] = useState("");
  const [accountMessage, setAccountMessage] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  useEffect(() => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    fetchTenant(token, params.id)
      .then(setTenant)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, [params.id]);

  const handleCreateAccount = async () => {
    const token = getAccessToken();
    if (!token || !tenant) return;
    setError(null);
    try {
      const result = await createTenantAccount(token, tenant.id, accountEmail);
      setAccountMessage(
        result.temporary_password
          ? `Compte créé — mot de passe temporaire : ${result.temporary_password}`
          : "Compte locataire créé",
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Création impossible");
    }
  };

  if (!tenant) {
    return (
      <ProtectedRoute>
        <AppHeader />
        <main className="mx-auto max-w-4xl px-6 py-10">
          <p className="text-muted-foreground">{error ?? "Chargement…"}</p>
        </main>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">
            {tenant.first_name} {tenant.last_name}
          </h1>
          <p className="mt-2 text-muted-foreground">{tenant.phone_primary}</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Info label="Profession" value={tenant.profession ?? "—"} />
          <Info
            label="Pièce d'identité"
            value={`${ID_DOCUMENT_LABELS[tenant.id_document_type]} — ${tenant.id_document_number}`}
          />
          <Info
            label="Mode de paiement"
            value={
              tenant.payment_method
                ? PAYMENT_METHOD_LABELS[tenant.payment_method]
                : "—"
            }
          />
          <Info
            label="Contact urgence"
            value={
              tenant.emergency_contact_name
                ? `${tenant.emergency_contact_name} (${tenant.emergency_contact_phone ?? ""})`
                : "—"
            }
          />
        </div>

        {tenant.current_lease && (
          <section className="rounded-xl border border-border bg-card shadow-sm p-6">
            <h2 className="text-lg font-semibold">Bail actuel</h2>
            <p className="mt-2 text-muted-foreground">
              {tenant.current_lease.building_name} — {tenant.current_lease.unit_code}
            </p>
            <p className="mt-1 font-medium">
              {formatCurrency(tenant.current_lease.rent_amount)} / mois
            </p>
            <p className="text-sm text-muted-foreground">
              Depuis le {tenant.current_lease.start_date}
            </p>
            <Link
              href={`/dashboard/baux/${tenant.current_lease.id}`}
              className="mt-3 inline-block text-sm font-medium underline"
            >
              Voir le bail
            </Link>
          </section>
        )}

        {canManage && !tenant.user_id && user?.role.code !== "gestionnaire" && (
          <section className="rounded-xl border border-border bg-card shadow-sm p-6">
            <h2 className="text-lg font-semibold">Compte espace locataire</h2>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <Input
                type="email"
                placeholder="Email du locataire"
                value={accountEmail}
                onChange={(e) => setAccountEmail(e.target.value)}
              />
              <Button onClick={handleCreateAccount}>Créer le compte</Button>
            </div>
            {accountMessage && (
              <p className="mt-3 text-sm text-emerald-700">{accountMessage}</p>
            )}
          </section>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}

        {tenant && (
          <DocumentLibrary
            entityType="tenant"
            entityId={tenant.id}
            canUpload={canManage}
          />
        )}

        <Link href="/dashboard/locataires" className="text-sm font-medium underline">
          Retour à la liste
        </Link>
      </main>
    </ProtectedRoute>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card shadow-sm p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}
