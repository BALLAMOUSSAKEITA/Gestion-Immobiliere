"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { DiffViewer } from "@/components/approvals/diff-viewer";
import { SuperAdminRoute } from "@/components/auth/super-admin-route";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  APPROVAL_ACTION_LABELS,
  APPROVAL_STATUS_LABELS,
  approveApprovalRequest,
  fetchApprovalRequest,
  rejectApprovalRequest,
  type ApprovalRequestDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useConfirm } from "@/contexts/confirm-context";
import { modifyConfirm } from "@/lib/confirm-presets";

export default function ValidationDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const confirm = useConfirm();
  const [request, setRequest] = useState<ApprovalRequestDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [processing, setProcessing] = useState(false);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    setRequest(await fetchApprovalRequest(token, params.id));
  }, [params.id]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  async function handleApprove() {
    const token = getAccessToken();
    if (!token || !params.id) return;
    if (!(await confirm(modifyConfirm("Approuver et exécuter cette demande ?")))) return;
    setProcessing(true);
    setError(null);
    try {
      await approveApprovalRequest(token, params.id, comment || undefined);
      router.push("/dashboard/validations");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Approbation impossible");
    } finally {
      setProcessing(false);
    }
  }

  async function handleReject() {
    const token = getAccessToken();
    if (!token || !params.id || !comment.trim()) {
      setError("Un commentaire est obligatoire pour rejeter.");
      return;
    }
    if (!(await confirm(modifyConfirm("Rejeter cette demande de validation ?")))) return;
    setProcessing(true);
    setError(null);
    try {
      await rejectApprovalRequest(token, params.id, comment.trim());
      router.push("/dashboard/validations");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Rejet impossible");
    } finally {
      setProcessing(false);
    }
  }

  return (
    <SuperAdminRoute>
      <div className="flex flex-col gap-6">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/validations">← Validations</Link>
        </Button>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {request && (
          <>
            <div>
              <h1 className="text-3xl font-bold">
                {APPROVAL_ACTION_LABELS[request.action_code] ?? request.action_code}
              </h1>
              <p className="mt-2 text-muted-foreground">
                {APPROVAL_STATUS_LABELS[request.status]} — demandé par{" "}
                {request.requested_by.full_name}
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card shadow-sm p-5">
              <p className="text-sm text-muted-foreground">Justification du demandeur</p>
              <p className="mt-1">{request.reason}</p>
              <p className="mt-4 text-sm text-muted-foreground">
                Entité : {request.entity_type} ({request.entity_id})
              </p>
            </div>

            <div>
              <h2 className="mb-3 text-lg font-semibold">Comparaison avant / après</h2>
              <DiffViewer before={request.payload_before} after={request.payload_after} />
            </div>

            {request.status === "pending" && (
              <div className="space-y-3 rounded-xl border border-border bg-card shadow-sm p-5">
                <label className="block text-sm font-medium">
                  Commentaire (obligatoire pour rejeter)
                </label>
                <Input
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Commentaire de validation ou motif de rejet"
                />
                <div className="flex gap-2">
                  <Button variant="outline" disabled={processing} onClick={handleReject}>
                    Rejeter
                  </Button>
                  <Button disabled={processing} onClick={handleApprove}>
                    Approuver et exécuter
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </SuperAdminRoute>
  );
}
