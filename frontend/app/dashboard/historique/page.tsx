"use client";

import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
  fetchAuditLogs,
  type AuditLogSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

export default function HistoriquePage() {
  const { user } = useAuth();
  const [items, setItems] = useState<AuditLogSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const canAccess =
    user?.role.code === "super_admin" || user?.role.code === "admin_familial";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchAuditLogs(token, { page_size: 50 });
    setItems(data.items);
  }, []);

  useEffect(() => {
    if (!canAccess) return;
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load, canAccess]);

  if (user && !canAccess) {
    return (
        <div className="flex flex-col gap-6">
          <p className="text-red-600">Accès réservé aux administrateurs.</p>
        </div>
    );
  }

  return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold">Historique des modifications</h1>
          <p className="mt-2 text-muted-foreground">
            Journal d&apos;audit immuable — qui a fait quoi, quand.
          </p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Utilisateur</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Entité</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-border">
                  <td className="px-4 py-3">
                    {new Date(item.created_at).toLocaleString("fr-FR")}
                  </td>
                  <td className="px-4 py-3">{item.user.full_name}</td>
                  <td className="px-4 py-3 font-medium">{item.action}</td>
                  <td className="px-4 py-3">
                    {item.entity_type} / {item.entity_id.slice(0, 8)}…
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.length === 0 && (
            <p className="p-6 text-center text-muted-foreground">Aucune entrée d&apos;audit.</p>
          )}
        </div>
      </div>
  );
}
