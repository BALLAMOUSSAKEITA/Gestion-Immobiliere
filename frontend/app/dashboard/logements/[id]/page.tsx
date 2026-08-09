"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { DocumentLibrary } from "@/components/documents/document-library";
import { UnitStatusBadge } from "@/components/buildings/unit-status-badge";
import { ImageUploadField } from "@/components/ui/image-upload-field";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  deleteUnitPhoto,
  fetchUnit,
  fetchUnitHistory,
  formatCurrency,
  uploadUnitPhoto,
  UNIT_TYPE_LABELS,
  type UnitDetail,
  type UnitHistoryItem,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";
import { useConfirm } from "@/contexts/confirm-context";
import { deleteConfirm, modifyConfirm } from "@/lib/confirm-presets";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function UnitDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const confirm = useConfirm();
  const [unit, setUnit] = useState<UnitDetail | null>(null);
  const [history, setHistory] = useState<UnitHistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const reloadUnit = async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    const data = await fetchUnit(token, params.id);
    setUnit(data);
  };

  useEffect(() => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    fetchUnit(token, params.id)
      .then(setUnit)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
    fetchUnitHistory(token, params.id)
      .then(setHistory)
      .catch(() => setHistory([]));
  }, [params.id]);

  return (
      <div className="flex flex-col gap-6">
        {!unit ? (
          <p className="text-muted-foreground">{error ?? "Chargement…"}</p>
        ) : (
          <>
            <div>
              <p className="text-sm text-muted-foreground">{unit.code}</p>
              <h1 className="text-3xl font-bold">
                {UNIT_TYPE_LABELS[unit.type]} {unit.number}
              </h1>
              <p className="mt-2 text-muted-foreground">
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
              <p className="rounded-xl border border-border bg-card shadow-sm p-4 text-foreground">
                {unit.description}
              </p>
            )}

            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <h2 className="mb-3 text-lg font-semibold">Photos du logement</h2>
              {unit.photos.length > 0 ? (
                <div className="mb-4 grid gap-3 sm:grid-cols-3">
                  {unit.photos.map((photo) => (
                    <div key={photo.id} className="relative">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={`${API_URL}${photo.url}`}
                        alt={unit.code}
                        className="aspect-video w-full rounded-lg border border-border object-cover"
                      />
                      {canManage && (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="absolute right-2 top-2 bg-background/90"
                          onClick={async () => {
                            const token = getAccessToken();
                            if (!token) return;
                            if (!(await confirm(deleteConfirm("cette photo")))) return;
                            await deleteUnitPhoto(token, unit.id, photo.id);
                            await reloadUnit();
                          }}
                        >
                          Supprimer
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mb-4 text-sm text-muted-foreground">
                  Aucune photo pour ce logement.
                </p>
              )}

              {canManage && (
                <ImageUploadField
                  embedded
                  label="Ajouter une photo"
                  hint="Visible sur les annonces publiques si le logement est publié."
                  multiple
                  onUpload={async (files) => {
                    const token = getAccessToken();
                    if (!token) return;
                    if (
                      !(await confirm(
                        modifyConfirm(
                          files.length > 1
                            ? `Ajouter ${files.length} photos au logement ?`
                            : "Ajouter une photo au logement ?",
                        ),
                      ))
                    ) {
                      return;
                    }
                    for (const file of files) {
                      await uploadUnitPhoto(token, unit.id, file);
                    }
                    await reloadUnit();
                  }}
                />
              )}
            </div>

            <DocumentLibrary
              entityType="unit"
              entityId={unit.id}
              canUpload={canManage}
            />

            {history.length > 0 && (
              <div className="rounded-xl border border-border bg-card p-4">
                <h2 className="mb-3 text-lg font-semibold">Historique des locataires</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm">
                    <thead className="border-b border-border text-muted-foreground">
                      <tr>
                        <th className="py-2 pr-4">Locataire</th>
                        <th className="py-2 pr-4">Entrée</th>
                        <th className="py-2 pr-4">Sortie</th>
                        <th className="py-2 pr-4">Loyer</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((entry) => (
                        <tr key={entry.id} className="border-b border-border">
                          <td className="py-2 pr-4">{entry.tenant_name ?? "—"}</td>
                          <td className="py-2 pr-4">
                            {new Date(entry.entry_date).toLocaleDateString("fr-FR")}
                          </td>
                          <td className="py-2 pr-4">
                            {entry.exit_date
                              ? new Date(entry.exit_date).toLocaleDateString("fr-FR")
                              : "En cours"}
                          </td>
                          <td className="py-2 pr-4">{formatCurrency(entry.rent_amount)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <Link
              href={`/dashboard/immeubles/${unit.building_id}`}
              className="text-sm font-medium underline"
            >
              Retour à l&apos;immeuble
            </Link>
          </>
        )}
      </div>
  );
}
