"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchReceipts,
  formatCurrency,
  type ReceiptSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function ReceiptsPage() {
  const [receipts, setReceipts] = useState<ReceiptSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchReceipts(token, { page_size: 50 })
      .then((data) => setReceipts(data.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Reçus</h1>
          <p className="mt-2 text-zinc-600">Justificatifs de paiement générés.</p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50">
              <tr>
                <th className="px-4 py-3">Numéro</th>
                <th className="px-4 py-3">Locataire</th>
                <th className="px-4 py-3">Logement</th>
                <th className="px-4 py-3">Montant</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {receipts.map((receipt) => (
                <tr key={receipt.id} className="border-b border-zinc-100">
                  <td className="px-4 py-3 font-medium">{receipt.receipt_number}</td>
                  <td className="px-4 py-3">{receipt.tenant_name}</td>
                  <td className="px-4 py-3">{receipt.unit_code}</td>
                  <td className="px-4 py-3">{formatCurrency(receipt.amount)}</td>
                  <td className="px-4 py-3">
                    {new Date(receipt.issued_at).toLocaleDateString("fr-FR")}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/recus/${receipt.id}`}
                      className="font-medium underline"
                    >
                      Voir
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {receipts.length === 0 && !error && (
            <p className="p-6 text-center text-zinc-500">Aucun reçu.</p>
          )}
        </div>

        <Button asChild variant="outline" className="self-start">
          <Link href="/dashboard/paiements">Voir les paiements</Link>
        </Button>
      </main>
    </ProtectedRoute>
  );
}
