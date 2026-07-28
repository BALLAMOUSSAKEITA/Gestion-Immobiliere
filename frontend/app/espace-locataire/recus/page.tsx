"use client";

import { useEffect, useState } from "react";

import { ApiError, fetchTenantReceipts, formatCurrency, type ReceiptSummary } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function TenantReceiptsPage() {
  const [items, setItems] = useState<ReceiptSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchTenantReceipts(token)
      .then((data) => setItems(data.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold">Mes reçus</h1>
        <p className="mt-2 text-muted-foreground">Téléchargez vos reçus de paiement.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="rounded-xl border border-border bg-card shadow-sm px-4 py-8 text-center text-muted-foreground">
            Aucun reçu disponible.
          </p>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className="flex flex-col gap-2 rounded-xl border border-border bg-card shadow-sm p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="font-semibold">{item.receipt_number}</p>
                <p className="text-sm text-muted-foreground">
                  {new Date(item.issued_at).toLocaleDateString("fr-FR")} · {formatCurrency(item.amount)}
                </p>
              </div>
              <a
                href={`${API_URL}${item.pdf_url}`}
                target="_blank"
                rel="noreferrer"
                className="text-sm font-medium text-blue-600 hover:underline"
              >
                Télécharger PDF
              </a>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
