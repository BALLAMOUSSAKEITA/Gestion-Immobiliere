"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchSharedDocument } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SharedDocumentPage() {
  const params = useParams<{ token: string }>();
  const [doc, setDoc] = useState<{
    title: string;
    file_name: string;
    mime_type: string;
    download_url: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.token) return;
    fetchSharedDocument(params.token)
      .then(setDoc)
      .catch(() => setError("Lien invalide ou expiré"));
  }, [params.token]);

  if (error) {
    return (
      <main className="mx-auto max-w-lg px-6 py-16 text-center">
        <p className="text-red-600">{error}</p>
      </main>
    );
  }

  if (!doc) {
    return (
      <main className="mx-auto max-w-lg px-6 py-16 text-center">
        <p className="text-zinc-500">Chargement…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-16">
      <h1 className="text-2xl font-bold">{doc.title}</h1>
      <a
        href={`${API_BASE}${doc.download_url}`}
        className="inline-flex w-fit rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white"
      >
        Télécharger {doc.file_name}
      </a>
      {(doc.mime_type.startsWith("image/") || doc.mime_type === "application/pdf") && (
        <iframe
          src={`${API_BASE}${doc.download_url}`}
          title={doc.title}
          className="h-[70vh] w-full rounded-xl border border-zinc-200"
        />
      )}
    </main>
  );
}
