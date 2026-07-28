"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  fetchTenantMessages,
  sendTenantMessage,
  type PortalMessageSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function TenantMessagesPage() {
  const [items, setItems] = useState<PortalMessageSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchTenantMessages(token);
    setItems(data.items);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const token = getAccessToken();
    if (!token) return;
    setSending(true);
    setError(null);
    try {
      await sendTenantMessage(token, { subject, body });
      setSubject("");
      setBody("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Envoi impossible");
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="flex flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Messages</h1>
        <p className="mt-2 text-muted-foreground">Contactez votre gestionnaire.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSend} className="space-y-3 rounded-xl border border-border bg-card shadow-sm p-4">
        <Input
          required
          placeholder="Sujet"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
        />
        <textarea
          required
          rows={4}
          placeholder="Votre message"
          className="w-full rounded-md border border-input px-3 py-2 text-sm"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        <Button type="submit" disabled={sending}>
          {sending ? "Envoi…" : "Envoyer"}
        </Button>
      </form>

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="rounded-xl border border-border bg-card shadow-sm px-4 py-8 text-center text-muted-foreground">
            Aucun message pour le moment.
          </p>
        ) : (
          items.map((item) => (
            <div key={item.id} className="rounded-xl border border-border bg-card shadow-sm p-4">
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold">{item.subject}</p>
                {!item.is_read && (
                  <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
                    Nouveau
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                {item.sender_name} · {new Date(item.created_at).toLocaleDateString("fr-FR")}
              </p>
              <p className="mt-2 text-foreground">{item.body}</p>
            </div>
          ))
        )}
      </div>
    </main>
  );
}
