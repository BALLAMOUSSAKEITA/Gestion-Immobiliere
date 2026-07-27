"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { RequestApprovalModal } from "@/components/approvals/request-approval-modal";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  deleteDocumentWithApproval,
  fetchDocument,
  formatFileSize,
  shareDocument,
  type DocumentDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [previewSrc, setPreviewSrc] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteSuccess, setDeleteSuccess] = useState<string | null>(null);

  const isSuperAdmin = user?.role.code === "super_admin";
  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    setDocument(await fetchDocument(token, params.id));
  }, [params.id]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  useEffect(() => {
    const token = getAccessToken();
    if (!document || !token) return;
    if (
      !document.mime_type.startsWith("image/") &&
      document.mime_type !== "application/pdf"
    ) {
      return;
    }
    let objectUrl: string | null = null;
    let cancelled = false;
    fetch(`${API_BASE}/api/v1/documents/${document.id}/preview`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Preview failed");
        return res.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setPreviewSrc(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setPreviewSrc(null);
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [document?.id, document?.mime_type]);

  async function handleShare() {
    const token = getAccessToken();
    if (!token || !params.id) return;
    const share = await shareDocument(token, params.id);
    setShareUrl(`${window.location.origin}${share.share_url}`);
  }

  async function handleDirectDelete() {
    const token = getAccessToken();
    if (!token || !params.id) return;
    if (!window.confirm("Supprimer définitivement ce document ?")) return;
    setError(null);
    try {
      await deleteDocumentWithApproval(token, params.id);
      router.push("/dashboard/documents");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Suppression impossible");
    }
  }

  function handleDeleteRequested() {
    setDeleteSuccess("Demande de suppression envoyée au super administrateur.");
    setShowDeleteModal(false);
  }

  const token = getAccessToken();

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/documents">← Bibliothèque</Link>
        </Button>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {document && (
          <>
            <div>
              <h1 className="text-3xl font-bold">{document.title}</h1>
              <p className="mt-2 text-zinc-600">
                {document.document_type_label} — {formatFileSize(document.file_size)}
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {token && (
                <Button asChild>
                  <a
                    href={`${API_BASE}/api/v1/documents/${document.id}/download`}
                    onClick={(e) => {
                      e.preventDefault();
                      fetch(`${API_BASE}/api/v1/documents/${document.id}/download`, {
                        headers: { Authorization: `Bearer ${token}` },
                      })
                        .then((res) => res.blob())
                        .then((blob) => {
                          const url = URL.createObjectURL(blob);
                          const a = window.document.createElement("a");
                          a.href = url;
                          a.download = document.file_name;
                          a.click();
                          URL.revokeObjectURL(url);
                        });
                    }}
                  >
                    Télécharger
                  </a>
                </Button>
              )}
              {canManage && (
                <Button variant="outline" onClick={handleShare}>
                  Partager
                </Button>
              )}
              {canManage && isSuperAdmin && (
                <Button variant="outline" onClick={handleDirectDelete}>
                  Supprimer
                </Button>
              )}
              {canManage && !isSuperAdmin && (
                <Button variant="outline" onClick={() => setShowDeleteModal(true)}>
                  Demander suppression
                </Button>
              )}
              {document.mime_type.startsWith("image/") || document.mime_type === "application/pdf" ? (
                <Button variant="outline" onClick={() => window.print()}>
                  Imprimer
                </Button>
              ) : null}
            </div>

            {deleteSuccess && (
              <p className="rounded-md bg-blue-50 px-4 py-3 text-sm text-blue-800">
                {deleteSuccess}
              </p>
            )}

            {shareUrl && (
              <p className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-800">
                Lien de partage : {shareUrl}
              </p>
            )}

            {previewSrc && document.mime_type.startsWith("image/") && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={previewSrc}
                alt={document.title}
                className="max-h-[600px] rounded-xl border border-zinc-200"
              />
            )}

            {previewSrc && document.mime_type === "application/pdf" && (
              <iframe
                src={previewSrc}
                title={document.title}
                className="h-[600px] w-full rounded-xl border border-zinc-200"
              />
            )}

            {document.description && (
              <p className="text-sm text-zinc-600">{document.description}</p>
            )}
          </>
        )}

        {document && (
          <RequestApprovalModal
            open={showDeleteModal}
            onClose={() => setShowDeleteModal(false)}
            onSuccess={handleDeleteRequested}
            actionCode="document.delete"
            entityType="document"
            entityId={document.id}
            title="Demander la suppression du document"
          />
        )}
      </main>
    </ProtectedRoute>
  );
}
