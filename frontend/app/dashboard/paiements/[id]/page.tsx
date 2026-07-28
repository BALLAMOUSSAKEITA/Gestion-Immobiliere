"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchPayment,
  formatCurrency,
  PAYMENT_METHOD_LABELS,
  type PaymentDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function PaymentDetailPage() {
  const params = useParams<{ id: string }>();
  const [payment, setPayment] = useState<PaymentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    fetchPayment(token, params.id)
      .then(setPayment)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, [params.id]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10">
        {!payment ? (
          <p className="text-muted-foreground">{error ?? "Chargement…"}</p>
        ) : (
          <>
            <div>
              <h1 className="text-3xl font-bold">
                Paiement — {formatCurrency(payment.amount)}
              </h1>
              <p className="mt-2 text-muted-foreground">
                {payment.tenant_name} · {payment.unit_code}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Info label="Date" value={payment.payment_date} />
              <Info
                label="Mode"
                value={PAYMENT_METHOD_LABELS[payment.payment_method]}
              />
              <Info label="Enregistré par" value={payment.recorded_by_name} />
              <Info label="Statut" value={payment.status} />
              {payment.reference && (
                <Info label="Référence" value={payment.reference} />
              )}
            </div>

            {payment.allocations.length > 0 && (
              <div className="rounded-xl border border-border bg-card shadow-sm p-4">
                <p className="font-medium">Allocations</p>
                <ul className="mt-2 space-y-1 text-sm">
                  {payment.allocations.map((item) => (
                    <li key={`${item.period_year}-${item.period_month}`}>
                      {String(item.period_month).padStart(2, "0")}/{item.period_year} —{" "}
                      {formatCurrency(item.allocated_amount)}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {payment.receipt_id && (
              <div className="flex flex-wrap gap-3">
                <Button asChild>
                  <Link href={`/dashboard/recus/${payment.receipt_id}`}>
                    Voir le reçu {payment.receipt_number}
                  </Link>
                </Button>
              </div>
            )}

            <Link href="/dashboard/paiements" className="text-sm font-medium underline">
              Retour à la liste
            </Link>
          </>
        )}
      </main>
    </ProtectedRoute>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card shadow-sm p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}
