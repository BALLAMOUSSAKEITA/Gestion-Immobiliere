"use client";

import { useEffect, useState } from "react";

import {
  ApiError,
  fetchTenantPayments,
  formatCurrency,
  PAYMENT_METHOD_LABELS,
  type PaymentSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function TenantPaymentsPage() {
  const [items, setItems] = useState<PaymentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchTenantPayments(token)
      .then((data) => setItems(data.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <main className="flex flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Mes paiements</h1>
        <p className="mt-2 text-muted-foreground">Historique de vos règlements de loyer.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-border bg-muted/50">
            <tr>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Montant</th>
              <th className="px-4 py-3">Méthode</th>
              <th className="px-4 py-3">Statut</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                  Aucun paiement enregistré.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-b border-border">
                  <td className="px-4 py-3">{item.payment_date}</td>
                  <td className="px-4 py-3 font-medium">{formatCurrency(item.amount)}</td>
                  <td className="px-4 py-3">
                    {PAYMENT_METHOD_LABELS[item.payment_method] ?? item.payment_method}
                  </td>
                  <td className="px-4 py-3 capitalize">{item.status}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
