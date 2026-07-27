"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { DocumentLibrary } from "@/components/documents/document-library";
import { UnitStatusBadge } from "@/components/buildings/unit-status-badge";
import { AppHeader } from "@/components/layout/app-header";
import {
  ApiError,
  fetchUnit,
  formatCurrency,
  UNIT_TYPE_LABELS,
  type UnitDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function UnitDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const [unit, setUnit] = useState<UnitDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  useEffect(() => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    fetchUnit(token, params.id)
      .then(setUnit)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, [params.id]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10">
        {!unit ? (
          <p className="text-zinc-500">{error ?? "Chargement…"}</p>
        ) : (
          <>
            <div>
              <p className="text-sm text-zinc-500">{unit.code}</p>
              <h1 className="text-3xl font-bold">
                {UNIT_TYPE_LABELS[unit.type]} {unit.number}
              </h1>
              <p className="mt-2 text-zinc-600">
                {unit.building_name} · {unit.commune}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <UnitStatusBadge status={unit.status} />
              <span className="text-lg font-semibold">
                {formatCurrency(unit.rent_amount)} / mois
              </span>
              {unit.is_public_listing && (
                <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700">
                  Annonce publique
                </span>
              )}
            </div>

            {unit.description && (
              <p className="rounded-xl border border-zinc-200 bg-white p-4 text-zinc-700">
                {unit.description}
              </p>
            )}

            {unit.photos.length > 0 && (
              <div className="grid gap-3 sm:grid-cols-3">
                {unit.photos.map((photo) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    key={photo.id}
                    src={`${API_URL}${photo.url}`}
                    alt={unit.code}
                    className="aspect-video rounded-lg object-cover"
                  />
                ))}
              </div>
            )}

            <DocumentLibrary
              entityType="unit"
              entityId={unit.id}
              canUpload={canManage}
            />

            <Link
              href={`/dashboard/immeubles/${unit.building_id}`}
              className="text-sm font-medium underline"
            >
              Retour à l&apos;immeuble
            </Link>
          </>
        )}
      </main>
    </ProtectedRoute>
  );
}
