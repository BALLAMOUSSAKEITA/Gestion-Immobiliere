"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import { ApiError, fetchReport, getReportDownloadUrl, type ReportDetail } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RapportDetailPage() {
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    setReport(await fetchReport(token, params.id));
  }, [params.id]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  async function download(format: "pdf" | "excel") {
    const token = getAccessToken();
    if (!token || !params.id) return;
    const url = `${API_BASE}${getReportDownloadUrl(params.id, format)}`;
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = `rapport-${params.id}.${format === "pdf" ? "pdf" : "xlsx"}`;
    a.click();
    URL.revokeObjectURL(objectUrl);
  }

  const kpis = (report?.data?.kpis ?? {}) as Record<string, unknown>;

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/rapports">← Rapports</Link>
        </Button>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {report && (
          <>
            <div>
              <h1 className="text-3xl font-bold capitalize">Rapport {report.report_type}</h1>
              <p className="mt-2 text-muted-foreground">
                {report.period_start} → {report.period_end}
              </p>
            </div>

            <div className="flex gap-2">
              {report.pdf_url && (
                <Button onClick={() => download("pdf")}>Télécharger PDF</Button>
              )}
              {report.excel_url && (
                <Button variant="outline" onClick={() => download("excel")}>
                  Télécharger Excel
                </Button>
              )}
            </div>

            <div className="rounded-xl border border-border bg-card shadow-sm p-5">
              <h2 className="mb-3 text-lg font-semibold">Résumé KPI</h2>
              <dl className="grid gap-2 text-sm sm:grid-cols-2">
                {Object.entries(kpis).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-4 border-b border-border py-1">
                    <dt className="text-muted-foreground">{key}</dt>
                    <dd className="font-medium">{String(value ?? "—")}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </>
        )}
      </main>
    </ProtectedRoute>
  );
}
