"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  APPROVAL_ACTION_LABELS,
  APPROVAL_STATUS_LABELS,
  cancelApprovalRequest,
  fetchMyApprovalRequests,
  type ApprovalRequestSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

export default function MesDemandesPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<ApprovalRequestSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const canAccess =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchMyApprovalRequests(token, { page_size: 50 });
    setItems(data.items);
  }, []);

  useEffect(() => {
    if (!canAccess) return;
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load, canAccess]);

  async function handleCancel(requestId: string) {
    const token = getAccessToken();
    if (!token) return;
    setCancellingId(requestId);
    setError(null);
    try {
      await cancelApprovalRequest(token, requestId);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Annulation impossible");
    } finally {
      setCancellingId(null);
    }
  }

  if (user && !canAccess) {
    return (
      <ProtectedRoute>
        <AppHeader />
        <main className="mx-auto max-w-4xl px-6 py-10">
          <p className="text-red-600">Accès non autorisé.</p>
        </main>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Mes demandes de validation</h1>
          <p className="mt-2 text-zinc-600">
            Suivi de vos actions sensibles en attente ou traitées.
          </p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="space-y-4">
          {items.length === 0 ? (
            <p className="rounded-xl border border-zinc-200 bg-white px-4 py-8 text-center text-zinc-500">
              Aucune demande soumise.
            </p>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-5 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-semibold">
                    {APPROVAL_ACTION_LABELS[item.action_code] ?? item.action_code}
                  </p>
                  <p className="mt-1 text-sm text-zinc-600">{item.reason}</p>
                  <p className="mt-2 text-xs text-zinc-500">
                    {APPROVAL_STATUS_LABELS[item.status]} —{" "}
                    {new Date(item.requested_at).toLocaleString("fr-FR")}
                  </p>
                  {item.review_comment && (
                    <p className="mt-1 text-sm text-zinc-600">
                      Réponse : {item.review_comment}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  {item.status === "pending" && (
                    <Button
                      variant="outline"
                      disabled={cancellingId === item.id}
                      onClick={() => handleCancel(item.id)}
                    >
                      Annuler
                    </Button>
                  )}
                  {user?.role.code === "super_admin" && (
                    <Button asChild variant="outline">
                      <Link href={`/dashboard/validations/${item.id}`}>Voir</Link>
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
