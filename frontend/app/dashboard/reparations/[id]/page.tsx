"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { RepairStatusBadge } from "@/components/repairs/repair-status-badge";
import { UrgencyBadge } from "@/components/repairs/urgency-badge";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  cancelRepair,
  completeRepair,
  fetchRepair,
  fetchRepairHistory,
  formatCurrency,
  REPAIR_STATUS_LABELS,
  updateRepairStatus,
  uploadRepairAttachment,
  type RepairDetail,
  type RepairHistoryItem,
  type RepairStatus,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

const NEXT_STATUS: Partial<Record<RepairStatus, RepairStatus>> = {
  new: "under_review",
  under_review: "technician_assigned",
  technician_assigned: "in_progress",
  in_progress: "completed",
};

export default function RepairDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const [repair, setRepair] = useState<RepairDetail | null>(null);
  const [history, setHistory] = useState<RepairHistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [finalCost, setFinalCost] = useState("");
  const [cancelReason, setCancelReason] = useState("");
  const [processing, setProcessing] = useState(false);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    const [detail, hist] = await Promise.all([
      fetchRepair(token, params.id),
      canManage ? fetchRepairHistory(token, params.id).catch(() => []) : Promise.resolve([]),
    ]);
    setRepair(detail);
    setHistory(hist);
  }, [params.id, canManage]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  async function handleNextStatus() {
    if (!repair) return;
    const next = NEXT_STATUS[repair.status];
    if (!next) return;
    const token = getAccessToken();
    if (!token) return;
    setProcessing(true);
    try {
      if (next === "completed") {
        if (!finalCost) {
          setError("Indiquez le coût final pour clôturer.");
          return;
        }
        await completeRepair(token, repair.id, {
          final_cost: finalCost,
          create_expense: true,
          notes: "Clôture depuis le tableau de bord",
        });
      } else {
        await updateRepairStatus(token, repair.id, { status: next });
      }
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action impossible");
    } finally {
      setProcessing(false);
    }
  }

  async function handleCancel() {
    if (!repair || !cancelReason.trim()) return;
    const token = getAccessToken();
    if (!token) return;
    setProcessing(true);
    try {
      await cancelRepair(token, repair.id, cancelReason.trim());
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Annulation impossible");
    } finally {
      setProcessing(false);
    }
  }

  async function handleUpload(file: File) {
    const token = getAccessToken();
    if (!token || !params.id) return;
    setProcessing(true);
    try {
      const updated = await uploadRepairAttachment(token, params.id, file);
      setRepair(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload impossible");
    } finally {
      setProcessing(false);
    }
  }

  const nextStatus = repair ? NEXT_STATUS[repair.status] : undefined;

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/reparations">← Retour aux réparations</Link>
        </Button>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {repair && (
          <>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h1 className="text-3xl font-bold">{repair.title}</h1>
                <p className="mt-2 text-zinc-600">
                  {repair.unit_code} — {repair.building_name}
                </p>
              </div>
              <div className="flex gap-2">
                <UrgencyBadge urgency={repair.urgency} />
                <RepairStatusBadge status={repair.status} />
              </div>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-white p-6">
              <p className="text-sm text-zinc-500">Description</p>
              <p className="mt-1">{repair.description}</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 text-sm">
                <div>
                  <p className="text-zinc-500">Signalé par</p>
                  <p>{repair.reported_by_name}</p>
                </div>
                <div>
                  <p className="text-zinc-500">Assigné à</p>
                  <p>{repair.assigned_to_name ?? "Non assigné"}</p>
                </div>
                {repair.final_cost && (
                  <div>
                    <p className="text-zinc-500">Coût final</p>
                    <p className="font-semibold">{formatCurrency(repair.final_cost)}</p>
                  </div>
                )}
                {repair.expense_id && (
                  <div>
                    <p className="text-zinc-500">Dépense liée</p>
                    <Link href={`/dashboard/depenses/${repair.expense_id}`} className="text-blue-600 hover:underline">
                      Voir la dépense
                    </Link>
                  </div>
                )}
              </div>
            </div>

            {canManage &&
              repair.status !== "completed" &&
              repair.status !== "cancelled" && (
                <div className="rounded-xl border border-zinc-200 bg-white p-6">
                  <h2 className="text-lg font-semibold">Actions</h2>
                  {nextStatus && (
                    <div className="mt-4 space-y-3">
                      {nextStatus === "completed" && (
                        <input
                          type="number"
                          min="1"
                          placeholder="Coût final (FCFA)"
                          value={finalCost}
                          onChange={(e) => setFinalCost(e.target.value)}
                          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
                        />
                      )}
                      <Button disabled={processing} onClick={handleNextStatus}>
                        Passer à « {REPAIR_STATUS_LABELS[nextStatus]} »
                        {nextStatus === "completed" ? " et clôturer" : ""}
                      </Button>
                    </div>
                  )}
                  <div className="mt-4 border-t border-zinc-100 pt-4">
                    <textarea
                      value={cancelReason}
                      onChange={(e) => setCancelReason(e.target.value)}
                      placeholder="Raison de l'annulation"
                      rows={2}
                      className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
                    />
                    <Button
                      variant="outline"
                      className="mt-2"
                      disabled={processing || !cancelReason.trim()}
                      onClick={handleCancel}
                    >
                      Annuler la demande
                    </Button>
                  </div>
                </div>
              )}

            <div className="rounded-xl border border-zinc-200 bg-white p-6">
              <h2 className="text-lg font-semibold">Pièces jointes</h2>
              {repair.attachments.length === 0 ? (
                <p className="mt-2 text-sm text-zinc-500">Aucune pièce jointe.</p>
              ) : (
                <ul className="mt-3 space-y-2 text-sm">
                  {repair.attachments.map((item) => (
                    <li key={item.id}>
                      <a
                        href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${item.file_url}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        {item.file_type} — {item.uploaded_by_name}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
              {(canManage || user?.role.code === "locataire") &&
                repair.status !== "completed" &&
                repair.status !== "cancelled" && (
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png,.webp,.mp4,.mov"
                    disabled={processing}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) void handleUpload(file);
                    }}
                    className="mt-4 text-sm"
                  />
                )}
            </div>

            {history.length > 0 && (
              <div className="rounded-xl border border-zinc-200 bg-white p-6">
                <h2 className="text-lg font-semibold">Historique</h2>
                <ul className="mt-4 space-y-3">
                  {history.map((item) => (
                    <li key={item.id} className="border-l-2 border-zinc-200 pl-4 text-sm">
                      <p className="font-medium">
                        {item.old_status ? `${item.old_status} → ${item.new_status}` : item.new_status}
                      </p>
                      <p className="text-zinc-500">
                        {item.changed_by_name} — {new Date(item.changed_at).toLocaleString("fr-FR")}
                      </p>
                      {item.comment && <p className="mt-1">{item.comment}</p>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </main>
    </ProtectedRoute>
  );
}
