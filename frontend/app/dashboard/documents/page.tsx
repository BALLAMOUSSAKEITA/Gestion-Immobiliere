"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
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
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Bibliothèque documentaire</h1>
          <p className="mt-2 text-zinc-600">Tous les documents centralisés de la plateforme.</p>
        </div>

        <div className="flex gap-2">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher…"
            className="flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm"
          />
          <Button onClick={() => load()}>Filtrer</Button>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <Link
              key={item.id}
              href={`/dashboard/documents/${item.id}`}
              className="rounded-xl border border-zinc-200 bg-white p-4 transition hover:border-zinc-300"
            >
              <p className="font-semibold">{item.title}</p>
              <p className="mt-1 text-sm text-zinc-500">{item.document_type_label}</p>
              <p className="mt-2 text-xs text-zinc-400">
                {formatFileSize(item.file_size)} — {item.entity_type}
              </p>
            </Link>
          ))}
        </div>
      </main>
    </ProtectedRoute>
  );
}
