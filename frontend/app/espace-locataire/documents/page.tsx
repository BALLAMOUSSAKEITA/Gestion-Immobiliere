"use client";

import { useEffect, useState } from "react";

import { ApiError, fetchTenantDocuments, type TenantDocumentItem } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function TenantDocumentsPage() {
  const [items, setItems] = useState<TenantDocumentItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchTenantDocuments(token)
      .then((data) => setItems(data.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold">Mes documents</h1>
        <p className="mt-2 text-muted-foreground">Contrats et documents partagés avec vous.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="rounded-xl border border-border bg-card shadow-sm px-4 py-8 text-center text-muted-foreground">
            Aucun document disponible.
          </p>
        ) : (
          items.map((item) => (
            <div key={item.id} className="rounded-xl border border-border bg-card shadow-sm p-4">
              <p className="font-semibold">{item.title}</p>
              <p className="text-sm text-muted-foreground">
                {item.file_name} · {new Date(item.uploaded_at).toLocaleDateString("fr-FR")}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
