"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchDocuments,
  formatFileSize,
  type DocumentSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function DocumentsPage() {
  const [items, setItems] = useState<DocumentSummary[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

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
          <p className="mt-2 text-muted-foreground">Tous les documents centralisés de la plateforme.</p>
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
            <Link
              key={item.id}
              href={`/dashboard/documents/${item.id}`}
              className="rounded-xl border border-border bg-card shadow-sm p-4 transition hover:border-input"
            >
              <p className="font-semibold">{item.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">{item.document_type_label}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                {formatFileSize(item.file_size)} — {item.entity_type}
              </p>
            </Link>
          ))}
        </div>
      </div>
  );
}
