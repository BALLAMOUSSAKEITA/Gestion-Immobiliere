"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { SuperAdminRoute } from "@/components/auth/super-admin-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  APPROVAL_ACTION_LABELS,
  APPROVAL_STATUS_LABELS,
  fetchApprovalRequests,
  type ApprovalRequestSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function ValidationsPage() {
  const [items, setItems] = useState<ApprovalRequestSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchApprovalRequests(token, {
      status: "pending",
      page_size: 50,
    });
    setItems(data.items);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
    <SuperAdminRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Validations en attente</h1>
          <p className="mt-2 text-zinc-600">
            Actions sensibles soumises par les gestionnaires et administrateurs.
          </p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50">
              <tr>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Entité</th>
                <th className="px-4 py-3">Demandeur</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-zinc-100">
                  <td className="px-4 py-3 font-medium">
                    {APPROVAL_ACTION_LABELS[item.action_code] ?? item.action_code}
                  </td>
                  <td className="px-4 py-3">
                    {item.entity_type} / {item.entity_id.slice(0, 8)}…
                  </td>
                  <td className="px-4 py-3">{item.requested_by.full_name}</td>
                  <td className="px-4 py-3">
                    {new Date(item.requested_at).toLocaleString("fr-FR")}
                  </td>
                  <td className="px-4 py-3">{APPROVAL_STATUS_LABELS[item.status]}</td>
                  <td className="px-4 py-3">
                    <Button asChild variant="outline">
                      <Link href={`/dashboard/validations/${item.id}`}>Traiter</Link>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.length === 0 && (
            <p className="p-6 text-center text-zinc-500">Aucune demande en attente.</p>
          )}
        </div>
      </main>
    </SuperAdminRoute>
  );
}
