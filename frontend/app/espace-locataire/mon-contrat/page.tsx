"use client";

import { useEffect, useState } from "react";

import {
  ApiError,
  fetchTenantLease,
  formatCurrency,
  type TenantLeaseInfo,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function TenantLeasePage() {
  const [lease, setLease] = useState<TenantLeaseInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchTenantLease(token)
      .then(setLease)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <main className="flex flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Mon contrat</h1>
        <p className="mt-2 text-zinc-600">Informations sur votre bail actif.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {lease && (
        <div className="space-y-4 rounded-xl border border-zinc-200 bg-white p-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-sm text-zinc-500">Début</p>
              <p className="font-medium">{lease.start_date}</p>
            </div>
            <div>
              <p className="text-sm text-zinc-500">Fin</p>
              <p className="font-medium">{lease.end_date ?? "—"}</p>
            </div>
            <div>
              <p className="text-sm text-zinc-500">Loyer</p>
              <p className="font-medium">{formatCurrency(lease.rent_amount)}</p>
            </div>
            <div>
              <p className="text-sm text-zinc-500">Caution</p>
              <p className="font-medium">{formatCurrency(lease.deposit_amount)}</p>
            </div>
            <div>
              <p className="text-sm text-zinc-500">Statut</p>
              <p className="font-medium capitalize">{lease.status}</p>
            </div>
          </div>
          {lease.contract_document_url && (
            <a
              href={lease.contract_document_url}
              target="_blank"
              rel="noreferrer"
              className="inline-block text-sm font-medium text-blue-600 hover:underline"
            >
              Télécharger le contrat
            </a>
          )}
        </div>
      )}
    </main>
  );
}
