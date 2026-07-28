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

export default function TenantNotificationsPage() {
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

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="mt-2 text-muted-foreground">Vos alertes et rappels.</p>
        </div>
        <Button variant="outline" onClick={() => markAllNotificationsRead(getAccessToken()!).then(load)}>
          Tout marquer lu
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="rounded-xl border border-border bg-card shadow-sm px-4 py-8 text-center text-muted-foreground">
            Aucune notification.
          </p>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className={`rounded-xl border border-border bg-card shadow-sm p-4 ${!item.is_read ? "border-blue-200 bg-blue-50/40" : ""}`}
            >
              <p className="font-semibold">{item.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">{item.body}</p>
              {!item.is_read && (
                <Button
                  variant="outline"
                  className="mt-3"
                  onClick={() => {
                    const token = getAccessToken();
                    if (!token) return;
                    markNotificationRead(token, item.id).then(load);
                  }}
                >
                  Marquer lu
                </Button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
