"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { PaymentForm } from "@/components/payments/payment-form";
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
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold">Enregistrer un paiement</h1>
          <p className="mt-2 text-muted-foreground">
            Choisissez la période de loyer réglée : le montant est calculé automatiquement et
            le reçu PDF est généré.
          </p>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <PaymentForm
          leases={leases}
          onSubmit={async (values) => {
            const token = getAccessToken();
            if (!token) return;
            const payment = await createPayment(token, values);
            router.push(`/dashboard/paiements/${payment.id}`);
          }}
        />
      </div>
  );
}
