"use client";

import { useRouter } from "next/navigation";

import { RepairForm } from "@/components/repairs/repair-form";
import { createRepair } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function TenantNewRepairPage() {
  const router = useRouter();

  return (
    <main className="flex flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Signaler une panne</h1>
        <p className="mt-2 text-zinc-600">
          Votre logement actif sera utilisé automatiquement pour la demande.
        </p>
      </div>
      <RepairForm
        showUnitSelect={false}
        onSubmit={async (values) => {
          const token = getAccessToken();
          if (!token) return;
          await createRepair(token, values);
          router.push("/espace-locataire/reparations");
        }}
      />
    </main>
  );
}
