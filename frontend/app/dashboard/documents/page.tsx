"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  deleteDocumentWithApproval,
  fetchDocuments,
  formatFileSize,
  type DocumentSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";
import { useConfirm } from "@/contexts/confirm-context";
import { deleteConfirm } from "@/lib/confirm-presets";

export default function DocumentsPage() {
  const { user } = useAuth();
  const confirm = useConfirm();
  const [items, setItems] = useState<DocumentSummary[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const isSuperAdmin = user?.role.code === "super_admin";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const params: Record<string, string | number> = { page_size: 50 };
    if (search) params.search = search;
    const data = await fetchDocuments(token, params);
    setItems(data.items);
  }, [search]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold">Bibliothèque documentaire</h1>
        <p className="mt-2 text-muted-foreground">
          Tous les documents centralisés de la plateforme.
        </p>
      </div>

      <div className="flex gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Rechercher…"
          className="flex-1 rounded-md border border-input px-3 py-2 text-sm"
        />
        <Button onClick={() => load()}>Filtrer</Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="rounded-xl border border-border bg-card p-4 shadow-sm"
          >
            <Link
              href={`/dashboard/documents/${item.id}`}
              className="block transition hover:opacity-80"
            >
              <p className="font-semibold">{item.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {item.document_type_label}
              </p>
              <p className="mt-2 text-xs text-muted-foreground">
                {formatFileSize(item.file_size)} — {item.entity_type}
              </p>
            </Link>
            {isSuperAdmin && (
              <Button
                variant="destructive"
                size="sm"
                className="mt-3"
                onClick={async () => {
                  if (!(await confirm(deleteConfirm(`le document « ${item.title} »`)))) {
                    return;
                  }
                  const token = getAccessToken();
                  if (!token) return;
                  setError(null);
                  try {
                    await deleteDocumentWithApproval(token, item.id);
                    await load();
                  } catch (err) {
                    setError(
                      err instanceof ApiError ? err.message : "Suppression impossible",
                    );
                  }
                }}
              >
                Supprimer
              </Button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
