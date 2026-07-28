"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { PaymentForm } from "@/components/payments/payment-form";
import { AppHeader } from "@/components/layout/app-header";
import {
  ApiError,
  createPayment,
  fetchLeases,
  type LeaseSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function NewPaymentPage() {
  const router = useRouter();
  const [leases, setLeases] = useState<LeaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchLeases(token, { status: "active", page_size: 100 })
      .then((data) => setLeases(data.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Enregistrer un paiement</h1>
          <p className="mt-2 text-muted-foreground">
            Le reçu PDF sera généré automatiquement.
          </p>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <PaymentForm
          leases={leases.map((lease) => ({
            id: lease.id,
            label: `${lease.tenant_name} — ${lease.unit_code}`,
          }))}
          onSubmit={async (values) => {
            const token = getAccessToken();
            if (!token) return;
            const payment = await createPayment(token, values);
            router.push(`/dashboard/paiements/${payment.id}`);
          }}
        />
      </main>
    </ProtectedRoute>
  );
}
