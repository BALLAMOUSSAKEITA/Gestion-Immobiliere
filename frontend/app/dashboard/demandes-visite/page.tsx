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
import { useConfirm } from "@/contexts/confirm-context";
import { modifyConfirm } from "@/lib/confirm-presets";

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  confirmed: "Confirmée",
  cancelled: "Annulée",
  completed: "Terminée",
};

export default function VisitRequestsPage() {
  const confirm = useConfirm();
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
    const label =
      status === "confirmed"
        ? "Confirmer cette demande de visite ?"
        : status === "cancelled"
          ? "Annuler cette demande de visite ?"
          : "Marquer cette visite comme terminée ?";
    if (!(await confirm(modifyConfirm(label)))) return;
    await updateVisitRequest(token, id, { status });
    await load();
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold">Demandes de visite</h1>
        <p className="mt-2 text-muted-foreground">
          Gérez les demandes de visite reçues depuis le portail public.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="rounded-xl border border-border bg-card shadow-sm px-4 py-8 text-center text-muted-foreground">
            Aucune demande pour le moment.
          </p>
        ) : (
          items.map((item) => (
            <div key={item.id} className="rounded-xl border border-border bg-card shadow-sm p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="font-semibold">{item.visitor_name}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.unit_code} · {item.visitor_email} · {item.visitor_phone}
                  </p>
                  {item.preferred_date && (
                    <p className="mt-1 text-sm">
                      Date souhaitée : {item.preferred_date}
                      {item.preferred_time ? ` à ${item.preferred_time}` : ""}
                    </p>
                  )}
                  {item.message && <p className="mt-2 text-sm text-foreground">{item.message}</p>}
                  <p className="mt-2 text-xs text-muted-foreground">
                    {new Date(item.created_at).toLocaleString("fr-FR")}
                  </p>
                </div>
                <div className="flex flex-col gap-2">
                  <span className="rounded-full bg-muted px-3 py-1 text-sm font-medium">
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
    </div>
  );
}
