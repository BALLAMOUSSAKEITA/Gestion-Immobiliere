"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchVisitRequests,
  updateVisitRequest,
  type VisitRequestSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  confirmed: "Confirmée",
  cancelled: "Annulée",
  completed: "Terminée",
};

export default function VisitRequestsPage() {
  const [items, setItems] = useState<VisitRequestSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchVisitRequests(token);
    setItems(data.items);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  async function handleStatusChange(id: string, status: string) {
    const token = getAccessToken();
    if (!token) return;
    await updateVisitRequest(token, id, { status });
    await load();
  }

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Demandes de visite</h1>
        <p className="mt-2 text-zinc-600">
          Gérez les demandes de visite reçues depuis le portail public.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="rounded-xl border border-zinc-200 bg-white px-4 py-8 text-center text-zinc-500">
            Aucune demande pour le moment.
          </p>
        ) : (
          items.map((item) => (
            <div key={item.id} className="rounded-xl border border-zinc-200 bg-white p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="font-semibold">{item.visitor_name}</p>
                  <p className="text-sm text-zinc-500">
                    {item.unit_code} · {item.visitor_email} · {item.visitor_phone}
                  </p>
                  {item.preferred_date && (
                    <p className="mt-1 text-sm">
                      Date souhaitée : {item.preferred_date}
                      {item.preferred_time ? ` à ${item.preferred_time}` : ""}
                    </p>
                  )}
                  {item.message && <p className="mt-2 text-sm text-zinc-700">{item.message}</p>}
                  <p className="mt-2 text-xs text-zinc-400">
                    {new Date(item.created_at).toLocaleString("fr-FR")}
                  </p>
                </div>
                <div className="flex flex-col gap-2">
                  <span className="rounded-full bg-zinc-100 px-3 py-1 text-sm font-medium">
                    {STATUS_LABELS[item.status] ?? item.status}
                  </span>
                  {item.status === "pending" && (
                    <div className="flex gap-2">
                      <Button onClick={() => handleStatusChange(item.id, "confirmed")}>
                        Confirmer
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleStatusChange(item.id, "cancelled")}
                      >
                        Annuler
                      </Button>
                    </div>
                  )}
                  {item.status === "confirmed" && (
                    <Button onClick={() => handleStatusChange(item.id, "completed")}>
                      Marquer terminée
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </main>
  );
}
