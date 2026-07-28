"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  fetchDocumentTypes,
  fetchDocuments,
  formatFileSize,
  uploadDocument,
  type DocumentEntityType,
  type DocumentSummary,
  type DocumentTypeItem,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

type DocumentLibraryProps = {
  entityType: DocumentEntityType;
  entityId: string;
  canUpload?: boolean;
  title?: string;
};

export function DocumentLibrary({
  entityType,
  entityId,
  canUpload = false,
  title = "Documents",
}: DocumentLibraryProps) {
  const [items, setItems] = useState<DocumentSummary[]>([]);
  const [types, setTypes] = useState<DocumentTypeItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [typeId, setTypeId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchDocuments(token, {
      entity_type: entityType,
      entity_id: entityId,
      page_size: 50,
    });
    setItems(data.items);
  }, [entityType, entityId]);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    Promise.all([load(), fetchDocumentTypes(token)])
      .then(([, docTypes]) => {
        setTypes(docTypes);
        setTypeId(docTypes[0]?.id ?? "");
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, [load]);

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token || !file || !typeId || !uploadTitle.trim()) return;
    setUploading(true);
    setError(null);
    try {
      await uploadDocument(token, {
        document_type_id: typeId,
        title: uploadTitle.trim(),
        entity_type: entityType,
        entity_id: entityId,
        file,
      });
      setUploadTitle("");
      setFile(null);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload impossible");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm p-6">
      <h2 className="text-lg font-semibold">{title}</h2>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      {canUpload && types.length > 0 && (
        <form onSubmit={handleUpload} className="mt-4 grid gap-3 border-b border-border pb-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <select
              value={typeId}
              onChange={(e) => setTypeId(e.target.value)}
              className="rounded-md border border-input px-3 py-2 text-sm"
            >
              {types.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.label}
                </option>
              ))}
            </select>
            <Input
              placeholder="Titre du document"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              required
            />
          </div>
          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.webp,.mp4"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
            className="text-sm"
          />
          <Button type="submit" disabled={uploading}>
            {uploading ? "Envoi…" : "Ajouter le document"}
          </Button>
        </form>
      )}

      <div className="mt-4 space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">Aucun document.</p>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className="flex flex-col gap-2 rounded-lg border border-border p-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="font-medium">{item.title}</p>
                <p className="text-xs text-muted-foreground">
                  {item.document_type_label} — {formatFileSize(item.file_size)} —{" "}
                  {new Date(item.uploaded_at).toLocaleDateString("fr-FR")}
                </p>
              </div>
              <Button asChild variant="outline">
                <Link href={`/dashboard/documents/${item.id}`}>Ouvrir</Link>
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
