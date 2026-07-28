"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { RepairForm } from "@/components/repairs/repair-form";
import { ApiError, createRepair, fetchUnits } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function NewRepairPage() {
  const router = useRouter();
  const [units, setUnits] = useState<{ id: string; label: string }[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchUnits(token, { page_size: 100 })
      .then((data) =>
        setUnits(data.items.map((unit) => ({ id: unit.id, label: `${unit.code} — ${unit.building_name}` }))),
      )
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold">Nouvelle réparation</h1>
          <p className="mt-2 text-muted-foreground">Déclarer une intervention sur un logement.</p>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {units.length > 0 && (
          <RepairForm
            units={units}
            onSubmit={async (values) => {
              const token = getAccessToken();
              if (!token) return;
              const repair = await createRepair(token, values);
              router.push(`/dashboard/reparations/${repair.id}`);
            }}
          />
        )}
      </div>
  );
}
