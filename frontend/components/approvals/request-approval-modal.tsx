"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, createApprovalRequest } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useConfirm } from "@/contexts/confirm-context";
import { modifyConfirm } from "@/lib/confirm-presets";

type RequestApprovalModalProps = {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  actionCode: string;
  entityType: string;
  entityId: string;
  title?: string;
};

export function RequestApprovalModal({
  open,
  onClose,
  onSuccess,
  actionCode,
  entityType,
  entityId,
  title = "Demander une validation",
}: RequestApprovalModalProps) {
  const confirm = useConfirm();
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!open) return null;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token || !reason.trim()) return;
    if (!(await confirm(modifyConfirm("Soumettre cette demande de validation ?")))) return;
    setSubmitting(true);
    setError(null);
    try {
      await createApprovalRequest(token, {
        action_code: actionCode,
        entity_type: entityType,
        entity_id: entityId,
        reason: reason.trim(),
      });
      setReason("");
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Envoi impossible");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Cette action nécessite l&apos;approbation du super administrateur.
        </p>
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Justification</label>
            <Input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Expliquez la raison de cette demande"
              required
              minLength={3}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Annuler
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Envoi…" : "Soumettre"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
