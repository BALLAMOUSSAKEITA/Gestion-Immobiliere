"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { BuildingForm } from "@/components/buildings/building-form";
import { UnitForm } from "@/components/buildings/unit-form";
import { UnitStatusBadge } from "@/components/buildings/unit-status-badge";
import { ImageUploadField } from "@/components/ui/image-upload-field";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  createBuildingUnit,
  deleteBuilding,
  deleteUnit,
  fetchBuilding,
  fetchBuildingUnits,
  fetchOwnerProfiles,
  fetchUsers,
  formatCurrency,
  releaseUnit,
  updateBuilding,
  uploadBuildingPhoto,
  type BuildingDetail,
  type OwnerProfile,
  type UnitSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";
import { useConfirm } from "@/contexts/confirm-context";
import { deleteConfirm, dangerConfirm, modifyConfirm } from "@/lib/confirm-presets";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function BuildingDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const confirm = useConfirm();
  const [building, setBuilding] = useState<BuildingDetail | null>(null);
  const [units, setUnits] = useState<UnitSummary[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [ownerProfiles, setOwnerProfiles] = useState<{ id: string; label: string }[]>([]);
  const [managers, setManagers] = useState<{ id: string; label: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" || user?.role.code === "admin_familial";
  const isSuperAdmin = user?.role.code === "super_admin";

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

  useEffect(() => {
    if (!canManage) return;
    const token = getAccessToken();
    if (!token) return;
    Promise.all([
      fetchOwnerProfiles(token),
      fetchUsers(token, { role: "gestionnaire", page_size: 100 }),
    ])
      .then(([profiles, users]) => {
        setOwnerProfiles(
          profiles.items.map((profile: OwnerProfile) => ({
            id: profile.id,
            label: `${profile.first_name} ${profile.last_name}`,
          })),
        );
        setManagers(
          users.items.map((userItem) => ({
            id: userItem.id,
            label: `${userItem.first_name} ${userItem.last_name}`,
          })),
        );
      })
      .catch(() => {
        /* les listes déroulantes restent vides si chargement impossible */
      });
  }, [canManage]);

  if (!building) {
    return (
        <div className="flex flex-col gap-6">
          {error ? (
            <p className="text-red-600">{error}</p>
          ) : (
            <p className="text-muted-foreground">Chargement…</p>
          )}
        </div>
    );
  }

  return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{building.code}</p>
            <h1 className="text-3xl font-bold">{building.name}</h1>
            <p className="mt-2 text-muted-foreground">
              {building.address} · {building.commune}
              {building.quartier ? ` · ${building.quartier}` : ""}
            </p>
          </div>
          <div className="flex flex-col items-start gap-3">
            {building.photo_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={`${API_URL}${building.photo_url}`}
                alt={building.name}
                className="h-48 w-full max-w-sm rounded-xl border border-border object-cover"
              />
            )}
            {canManage && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowEdit((value) => !value);
                  setActionError(null);
                }}
              >
                {showEdit ? "Annuler" : "Modifier l'immeuble"}
              </Button>
            )}
            {isSuperAdmin && (
              <Button
                variant="destructive"
                size="sm"
                onClick={async () => {
                  if (!(await confirm(deleteConfirm(`l'immeuble « ${building.name} »`)))) {
                    return;
                  }
                  const token = getAccessToken();
                  if (!token) return;
                  setActionError(null);
                  try {
                    await deleteBuilding(token, building.id);
                    router.push("/dashboard/immeubles");
                  } catch (err) {
                    setActionError(
                      err instanceof ApiError ? err.message : "Suppression impossible",
                    );
                  }
                }}
              >
                Supprimer l&apos;immeuble
              </Button>
            )}
          </div>
        </div>

        {actionError && <p className="text-sm text-red-600">{actionError}</p>}

        {showEdit && canManage && (
          <BuildingForm
            key={building.updated_at}
            ownerProfiles={ownerProfiles}
            managers={managers}
            submitLabel="Enregistrer les modifications"
            initialValues={{
              name: building.name,
              address: building.address,
              commune: building.commune,
              quartier: building.quartier ?? undefined,
              floor_count: building.floor_count,
              owner_profile_id: building.owner_profile_id ?? undefined,
              manager_user_id: building.manager_user_id ?? undefined,
              observations: building.observations ?? undefined,
            }}
            onSubmit={async (values) => {
              if (!(await confirm(modifyConfirm("Enregistrer les modifications de l'immeuble ?")))) {
                return;
              }
              const token = getAccessToken();
              if (!token) return;
              setActionError(null);
              try {
                const updated = await updateBuilding(token, building.id, values);
                setBuilding(updated);
                setShowEdit(false);
              } catch (err) {
                setActionError(
                  err instanceof ApiError ? err.message : "Modification impossible",
                );
                throw err;
              }
            }}
          />
        )}

        {building.observations && !showEdit && (
          <div className="rounded-xl border border-border bg-card shadow-sm p-4">
            <p className="text-sm text-muted-foreground">Observations</p>
            <p className="mt-1 whitespace-pre-wrap">{building.observations}</p>
          </div>
        )}

        {canManage && (
          <ImageUploadField
            label="Photo de l'immeuble"
            hint="Ajoutez une photo principale visible sur la liste et la fiche immeuble."
            onUpload={async (files) => {
              const token = getAccessToken();
              if (!token || !files[0]) return;
              if (!(await confirm(modifyConfirm("Mettre à jour la photo de l'immeuble ?")))) {
                return;
              }
              const updated = await uploadBuildingPhoto(token, building.id, files[0]);
              setBuilding(updated);
            }}
          />
        )}

        <div className="grid gap-4 sm:grid-cols-4">
          <Stat label="Logements" value={String(building.total_units)} />
          <Stat label="Occupés" value={String(building.occupied_units)} />
          <Stat label="Libres" value={String(building.free_units)} />
          <Stat
            label="Taux occupation"
            value={`${building.occupancy_rate}%`}
          />
        </div>

        <div className="rounded-xl border border-border bg-card shadow-sm p-4">
          <p className="text-sm text-muted-foreground">Loyers attendus / mois</p>
          <p className="text-2xl font-bold">
            {formatCurrency(building.monthly_expected_rent)}
          </p>
        </div>

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

        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Numéro</th>
                <th className="px-4 py-3">Loyer</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {units.map((unit) => (
                <tr key={unit.id} className="border-b border-border">
                  <td className="px-4 py-3 font-medium">{unit.code}</td>
                  <td className="px-4 py-3">{unit.number}</td>
                  <td className="px-4 py-3">{formatCurrency(unit.rent_amount)}</td>
                  <td className="px-4 py-3">
                    <UnitStatusBadge status={unit.status} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/dashboard/logements/${unit.id}`}
                        className="text-sm font-medium text-foreground underline"
                      >
                        Voir
                      </Link>
                      {isSuperAdmin &&
                        (unit.status === "occupied" || unit.status === "reserved") && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={async () => {
                              if (
                                !(await confirm(
                                  dangerConfirm(
                                    "Libérer le logement",
                                    `Cette action résilie immédiatement le bail actif et libère le logement ${unit.code}. Cette opération est irréversible.`,
                                    "Libérer le logement",
                                  ),
                                ))
                              ) {
                                return;
                              }
                              const token = getAccessToken();
                              if (!token) return;
                              setActionError(null);
                              try {
                                await releaseUnit(token, unit.id);
                                await loadData();
                              } catch (err) {
                                setActionError(
                                  err instanceof ApiError
                                    ? err.message
                                    : "Libération impossible",
                                );
                              }
                            }}
                          >
                            Libérer
                          </Button>
                        )}
                      {isSuperAdmin && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={async () => {
                            if (!(await confirm(deleteConfirm(`le logement ${unit.code}`)))) {
                              return;
                            }
                            const token = getAccessToken();
                            if (!token) return;
                            setActionError(null);
                            try {
                              await deleteUnit(token, unit.id);
                              await loadData();
                            } catch (err) {
                              setActionError(
                                err instanceof ApiError
                                  ? err.message
                                  : "Suppression impossible",
                              );
                            }
                          }}
                        >
                          Supprimer
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {units.length === 0 && (
            <p className="p-6 text-center text-muted-foreground">Aucun logement.</p>
          )}
        </div>
      </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card shadow-sm p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
