"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { LeaseStatusBadge } from "@/components/tenants/lease-status-badge";
import { DocumentLibrary } from "@/components/documents/document-library";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  fetchLease,
  formatCurrency,
  terminateLease,
  type LeaseDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";
import { useConfirm } from "@/contexts/confirm-context";
import { modifyConfirm } from "@/lib/confirm-presets";

export default function LeaseDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const confirm = useConfirm();
  const [lease, setLease] = useState<LeaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showTerminate, setShowTerminate] = useState(false);
  const [terminationDate, setTerminationDate] = useState("");
  const [terminationReason, setTerminationReason] = useState("");

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const loadLease = async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    const data = await fetchLease(token, params.id);
    setLease(data);
  };

  useEffect(() => {
    loadLease().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [params.id]);

  const handleTerminate = async () => {
    const token = getAccessToken();
    if (!token || !lease) return;
    if (!(await confirm(modifyConfirm("Terminer ce bail ?")))) return;
    setError(null);
    try {
      await terminateLease(token, lease.id, {
        termination_date: terminationDate,
        termination_reason: terminationReason,
      });
      setShowTerminate(false);
      await loadLease();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Résiliation impossible");
    }
  };

  if (!lease) {
    return (
        <div className="flex flex-col gap-6">
          <p className="text-muted-foreground">{error ?? "Chargement…"}</p>
        </div>
    );
  }

  return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-bold">Bail — {lease.unit_code}</h1>
          <LeaseStatusBadge status={lease.status} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Info label="Locataire" value={lease.tenant_name} />
          <Info label="Immeuble" value={lease.building_name} />
          <Info label="Loyer" value={`${formatCurrency(lease.rent_amount)} / mois`} />
          <Info
            label="Caution"
            value={`${formatCurrency(lease.deposit_amount)}${lease.deposit_paid ? " (payée)" : ""}`}
          />
          <Info label="Début" value={lease.start_date} />
          <Info label="Fin prévue" value={lease.end_date ?? "—"} />
        </div>

        {lease.status === "terminated" && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4">
            <p className="font-medium">Bail résilié le {lease.termination_date}</p>
            <p className="mt-1 text-sm text-muted-foreground">{lease.termination_reason}</p>
          </div>
        )}

        {canManage && lease.status === "active" && (
          <div>
            {!showTerminate ? (
              <Button variant="outline" onClick={() => setShowTerminate(true)}>
                Terminer le bail
              </Button>
            ) : (
              <div className="space-y-3 rounded-xl border border-border bg-card shadow-sm p-4">
                <Input
                  type="date"
                  value={terminationDate}
                  onChange={(e) => setTerminationDate(e.target.value)}
                />
                <Input
                  placeholder="Motif de résiliation"
                  value={terminationReason}
                  onChange={(e) => setTerminationReason(e.target.value)}
                />
                <div className="flex gap-2">
                  <Button onClick={handleTerminate}>Confirmer</Button>
                  <Button variant="outline" onClick={() => setShowTerminate(false)}>
                    Annuler
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}

        <DocumentLibrary
          entityType="lease"
          entityId={lease.id}
          canUpload={canManage}
        />

        <div className="flex gap-4">
          <Link
            href={`/dashboard/locataires/${lease.tenant_id}`}
            className="text-sm font-medium underline"
          >
            Voir le locataire
          </Link>
          <Link href="/dashboard/baux" className="text-sm font-medium underline">
            Retour aux baux
          </Link>
        </div>
      </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card shadow-sm p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}
