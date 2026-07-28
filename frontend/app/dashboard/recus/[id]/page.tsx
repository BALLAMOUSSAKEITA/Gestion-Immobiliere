"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchReceipt,
  formatCurrency,
  sendReceiptEmail,
  type ReceiptDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ReceiptDetailPage() {
  const params = useParams<{ id: string }>();
  const [receipt, setReceipt] = useState<ReceiptDetail | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token || !params.id) return;

    fetchReceipt(token, params.id)
      .then(setReceipt)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );

    fetch(`${API_URL}/api/v1/receipts/${params.id}/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("PDF indisponible");
        return res.blob();
      })
      .then((blob) => setPdfUrl(URL.createObjectURL(blob)))
      .catch(() => setPdfUrl(null));
  }, [params.id]);

  const handleSendEmail = async () => {
    const token = getAccessToken();
    if (!token || !receipt) return;
    try {
      const result = await sendReceiptEmail(token, receipt.id);
      setMessage(result.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Envoi impossible");
    }
  };

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10">
        {!receipt ? (
          <p className="text-muted-foreground">{error ?? "Chargement…"}</p>
        ) : (
          <>
            <div>
              <h1 className="text-3xl font-bold">{receipt.receipt_number}</h1>
              <p className="mt-2 text-muted-foreground">
                {receipt.tenant_name} · {receipt.unit_code} —{" "}
                {formatCurrency(receipt.amount)}
              </p>
            </div>

            {pdfUrl && (
              <iframe
                src={pdfUrl}
                title="Aperçu reçu"
                className="h-[600px] w-full rounded-xl border border-border"
              />
            )}

            <div className="flex flex-wrap gap-3">
              {pdfUrl && (
                <Button asChild>
                  <a href={pdfUrl} download={`${receipt.receipt_number}.pdf`}>
                    Télécharger PDF
                  </a>
                </Button>
              )}
              <Button variant="outline" onClick={handleSendEmail}>
                Envoyer par email
              </Button>
            </div>

            {message && <p className="text-sm text-emerald-700">{message}</p>}
            {error && <p className="text-sm text-red-600">{error}</p>}

            <Link href="/dashboard/recus" className="text-sm font-medium underline">
              Retour aux reçus
            </Link>
          </>
        )}
      </main>
    </ProtectedRoute>
  );
}
