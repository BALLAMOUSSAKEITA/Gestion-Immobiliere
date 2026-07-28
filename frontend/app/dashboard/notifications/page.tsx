"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchNotifications(token, 100);
    setItems(data.items);
  }

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, []);

  async function handleMarkRead(id: string) {
    const token = getAccessToken();
    if (!token) return;
    await markNotificationRead(token, id);
    await load();
  }

  async function handleMarkAll() {
    const token = getAccessToken();
    if (!token) return;
    await markAllNotificationsRead(token);
    await load();
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="mt-2 text-muted-foreground">Historique de vos alertes.</p>
        </div>
        <Button variant="outline" onClick={handleMarkAll}>
          Tout marquer lu
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="rounded-xl border border-border bg-card shadow-sm px-4 py-8 text-center text-muted-foreground">
            Aucune notification pour le moment.
          </p>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className={`rounded-xl border border-border bg-card shadow-sm p-4 ${!item.is_read ? "border-blue-200 bg-blue-50/40" : ""}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{item.title}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{item.body}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {new Date(item.created_at).toLocaleString("fr-FR")}
                  </p>
                </div>
                {!item.is_read && (
                  <Button variant="outline" onClick={() => handleMarkRead(item.id)}>
                    Lu
                  </Button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
