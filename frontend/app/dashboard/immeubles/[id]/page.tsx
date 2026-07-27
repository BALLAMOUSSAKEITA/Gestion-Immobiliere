"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { DocumentLibrary } from "@/components/documents/document-library";
import { UnitForm } from "@/components/buildings/unit-form";
import { UnitStatusBadge } from "@/components/buildings/unit-status-badge";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  createBuildingUnit,
  fetchBuilding,
  fetchBuildingUnits,
  formatCurrency,
  type BuildingDetail,
  type UnitSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function BuildingDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const [building, setBuilding] = useState<BuildingDetail | null>(null);
  const [units, setUnits] = useState<UnitSummary[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" || user?.role.code === "admin_familial";

  const loadData = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    const [buildingData, unitsData] = await Promise.all([
      fetchBuilding(token, params.id),
      fetchBuildingUnits(token, params.id),
    ]);
    setBuilding(buildingData);
    setUnits(unitsData.items);
  }, [params.id]);

  useEffect(() => {
    loadData().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [loadData]);

  if (!building) {
    return (
      <ProtectedRoute>
        <AppHeader />
        <main className="mx-auto max-w-6xl px-6 py-10">
          {error ? (
            <p className="text-red-600">{error}</p>
          ) : (
            <p className="text-zinc-500">Chargement…</p>
          )}
        </main>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm text-zinc-500">{building.code}</p>
            <h1 className="text-3xl font-bold">{building.name}</h1>
            <p className="mt-2 text-zinc-600">
              {building.address} · {building.commune}
              {building.quartier ? ` · ${building.quartier}` : ""}
            </p>
          </div>
          {building.photo_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={`${API_URL}${building.photo_url}`}
              alt={building.name}
              className="h-40 w-full max-w-xs rounded-xl object-cover"
            />
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-4">
          <Stat label="Logements" value={String(building.total_units)} />
          <Stat label="Occupés" value={String(building.occupied_units)} />
          <Stat label="Libres" value={String(building.free_units)} />
          <Stat
            label="Taux occupation"
            value={`${building.occupancy_rate}%`}
          />
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-4">
          <p className="text-sm text-zinc-500">Loyers attendus / mois</p>
          <p className="text-2xl font-bold">
            {formatCurrency(building.monthly_expected_rent)}
          </p>
        </div>

        <DocumentLibrary
          entityType="building"
          entityId={building.id}
          canUpload={canManage}
        />

        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Logements</h2>
          {canManage && (
            <Button onClick={() => setShowForm((value) => !value)}>
              {showForm ? "Annuler" : "Ajouter un logement"}
            </Button>
          )}
        </div>

        {showForm && canManage && (
          <UnitForm
            onSubmit={async (values) => {
              const token = getAccessToken();
              if (!token) return;
              await createBuildingUnit(token, building.id, values);
              setShowForm(false);
              await loadData();
            }}
          />
        )}

        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50">
              <tr>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Numéro</th>
                <th className="px-4 py-3">Loyer</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {units.map((unit) => (
                <tr key={unit.id} className="border-b border-zinc-100">
                  <td className="px-4 py-3 font-medium">{unit.code}</td>
                  <td className="px-4 py-3">{unit.number}</td>
                  <td className="px-4 py-3">{formatCurrency(unit.rent_amount)}</td>
                  <td className="px-4 py-3">
                    <UnitStatusBadge status={unit.status} />
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/logements/${unit.id}`}
                      className="text-sm font-medium text-zinc-900 underline"
                    >
                      Voir
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {units.length === 0 && (
            <p className="p-6 text-center text-zinc-500">Aucun logement.</p>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4">
      <p className="text-sm text-zinc-500">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
