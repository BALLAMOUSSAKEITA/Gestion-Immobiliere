"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  fetchBuildings,
  fetchOwnerProfiles,
  fetchTenants,
  fetchUsers,
  generateReport,
  type BuildingSummary,
  type OwnerProfile,
  type TenantSummary,
  type UserSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

const UNIT_TYPES = [
  { value: "", label: "Tous types" },
  { value: "apartment", label: "Appartement" },
  { value: "shop", label: "Magasin" },
  { value: "office", label: "Bureau" },
  { value: "other", label: "Autre" },
];

export default function GenererRapportPage() {
  const router = useRouter();
  const [periodStart, setPeriodStart] = useState("2026-07-01");
  const [periodEnd, setPeriodEnd] = useState("2026-07-31");
  const [reportType, setReportType] = useState("monthly");
  const [buildingId, setBuildingId] = useState("");
  const [ownerProfileId, setOwnerProfileId] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [managerUserId, setManagerUserId] = useState("");
  const [unitType, setUnitType] = useState("");
  const [buildings, setBuildings] = useState<BuildingSummary[]>([]);
  const [owners, setOwners] = useState<OwnerProfile[]>([]);
  const [tenants, setTenants] = useState<TenantSummary[]>([]);
  const [managers, setManagers] = useState<UserSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    Promise.all([
      fetchBuildings(token, { page_size: 100 }),
      fetchOwnerProfiles(token),
      fetchTenants(token, { page_size: 100 }),
      fetchUsers(token, { page_size: 100 }),
    ])
      .then(([b, o, t, u]) => {
        setBuildings(b.items);
        setOwners(o.items);
        setTenants(t.items);
        setManagers(u.items.filter((user) => user.role.code === "gestionnaire"));
      })
      .catch(() => undefined);
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const filters: Record<string, string> = {};
      if (buildingId) filters.building_id = buildingId;
      if (ownerProfileId) filters.owner_profile_id = ownerProfileId;
      if (tenantId) filters.tenant_id = tenantId;
      if (managerUserId) filters.manager_user_id = managerUserId;
      if (unitType) filters.unit_type = unitType;

      const report = await generateReport(token, {
        report_type: reportType,
        period_start: periodStart,
        period_end: periodEnd,
        export_formats: ["pdf", "excel"],
        filters: Object.keys(filters).length ? filters : undefined,
      });
      router.push(`/dashboard/rapports/${report.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Génération impossible");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Button asChild variant="outline" className="w-fit">
        <Link href="/dashboard/rapports">← Rapports</Link>
      </Button>

      <div>
        <h1 className="text-3xl font-bold">Générer un rapport</h1>
        <p className="mt-2 text-muted-foreground">
          Export PDF et Excel avec filtres par immeuble, propriétaire, locataire, gestionnaire ou type de logement.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-card p-5 shadow-sm">
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
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium">Début</label>
            <Input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} required />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Fin</label>
            <Input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} required />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium">Immeuble</label>
            <select
              value={buildingId}
              onChange={(e) => setBuildingId(e.target.value)}
              className="w-full rounded-md border border-input px-3 py-2 text-sm"
            >
              <option value="">Tous</option>
              {buildings.map((b) => (
                <option key={b.id} value={b.id}>{b.code} — {b.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Propriétaire</label>
            <select
              value={ownerProfileId}
              onChange={(e) => setOwnerProfileId(e.target.value)}
              className="w-full rounded-md border border-input px-3 py-2 text-sm"
            >
              <option value="">Tous</option>
              {owners.map((o) => (
                <option key={o.id} value={o.id}>{o.first_name} {o.last_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Locataire</label>
            <select
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              className="w-full rounded-md border border-input px-3 py-2 text-sm"
            >
              <option value="">Tous</option>
              {tenants.map((t) => (
                <option key={t.id} value={t.id}>{t.first_name} {t.last_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Gestionnaire</label>
            <select
              value={managerUserId}
              onChange={(e) => setManagerUserId(e.target.value)}
              className="w-full rounded-md border border-input px-3 py-2 text-sm"
            >
              <option value="">Tous</option>
              {managers.map((m) => (
                <option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Type de logement</label>
            <select
              value={unitType}
              onChange={(e) => setUnitType(e.target.value)}
              className="w-full rounded-md border border-input px-3 py-2 text-sm"
            >
              {UNIT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={loading}>
          {loading ? "Génération…" : "Générer PDF + Excel"}
        </Button>
      </form>
    </div>
  );
}
