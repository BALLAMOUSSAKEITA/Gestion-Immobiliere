"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { BuildingForm } from "@/components/buildings/building-form";
import { AppHeader } from "@/components/layout/app-header";
import {
  ApiError,
  createBuilding,
  fetchOwnerProfiles,
  fetchUsers,
  type OwnerProfile,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function NewBuildingPage() {
  const router = useRouter();
  const [ownerProfiles, setOwnerProfiles] = useState<
    { id: string; label: string }[]
  >([]);
  const [managers, setManagers] = useState<{ id: string; label: string }[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
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
          users.items.map((user) => ({
            id: user.id,
            label: `${user.first_name} ${user.last_name}`,
          })),
        );
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Nouvel immeuble</h1>
          <p className="mt-2 text-muted-foreground">
            Le code sera généré automatiquement (ex. KM001).
          </p>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <BuildingForm
          ownerProfiles={ownerProfiles}
          managers={managers}
          submitLabel="Créer l'immeuble"
          onSubmit={async (values) => {
            const token = getAccessToken();
            if (!token) return;
            const building = await createBuilding(token, values);
            router.push(`/dashboard/immeubles/${building.id}`);
          }}
        />
      </main>
    </ProtectedRoute>
  );
}
