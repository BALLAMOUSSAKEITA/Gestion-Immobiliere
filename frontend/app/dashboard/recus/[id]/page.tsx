"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchReceipt,
  formatCurrency,
  getReceiptWhatsAppLink,
  sendReceiptEmail,
  type ReceiptDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useConfirm } from "@/contexts/confirm-context";
import { modifyConfirm } from "@/lib/confirm-presets";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ReceiptDetailPage() {
  const confirm = useConfirm();
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
    if (!(await confirm(modifyConfirm("Envoyer ce reçu par email ?")))) return;
    try {
      const result = await sendReceiptEmail(token, receipt.id);
      setMessage(result.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Envoi impossible");
    }
  };

  const handleSendWhatsApp = async () => {
    const token = getAccessToken();
    if (!token || !receipt) return;
    if (!(await confirm(modifyConfirm("Ouvrir WhatsApp pour envoyer ce reçu ?")))) return;
    try {
      const result = await getReceiptWhatsAppLink(token, receipt.id);
      window.open(result.url, "_blank", "noopener,noreferrer");
      setMessage(result.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Envoi WhatsApp impossible");
    }
  };

  return (
      <div className="flex flex-col gap-6">
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
              <Button variant="outline" onClick={handleSendWhatsApp}>
                Envoyer par WhatsApp
              </Button>
            </div>

            {message && <p className="text-sm text-emerald-700">{message}</p>}
            {error && <p className="text-sm text-red-600">{error}</p>}

            <Link href="/dashboard/recus" className="text-sm font-medium underline">
              Retour aux reçus
            </Link>
          </>
        )}
      </div>
  );
}
