"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, generateReport } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function GenererRapportPage() {
  const router = useRouter();
  const [periodStart, setPeriodStart] = useState("2026-07-01");
  const [periodEnd, setPeriodEnd] = useState("2026-07-31");
  const [reportType, setReportType] = useState("monthly");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const report = await generateReport(token, {
        report_type: reportType,
        period_start: periodStart,
        period_end: periodEnd,
        export_formats: ["pdf", "excel"],
      });
      router.push(`/dashboard/rapports/${report.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Génération impossible");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-lg flex-col gap-6 px-6 py-10">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/rapports">← Rapports</Link>
        </Button>

        <div>
          <h1 className="text-3xl font-bold">Générer un rapport</h1>
          <p className="mt-2 text-muted-foreground">Export PDF et Excel.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-card shadow-sm p-5">
          <div>
            <label className="mb-1 block text-sm font-medium">Type</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full rounded-md border border-input px-3 py-2 text-sm"
            >
              <option value="daily">Journalier</option>
              <option value="weekly">Hebdomadaire</option>
              <option value="monthly">Mensuel</option>
              <option value="annual">Annuel</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Début</label>
            <Input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} required />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Fin</label>
            <Input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} required />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" disabled={loading}>
            {loading ? "Génération…" : "Générer PDF + Excel"}
          </Button>
        </form>
      </main>
    </ProtectedRoute>
  );
}
