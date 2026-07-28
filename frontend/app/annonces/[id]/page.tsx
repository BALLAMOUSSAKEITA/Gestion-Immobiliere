"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  createVisitRequest,
  fetchPublicUnit,
  formatCurrency,
  UNIT_TYPE_LABELS,
  type PublicUnitDetail,
} from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PublicUnitPage() {
  const params = useParams<{ id: string }>();
  const [unit, setUnit] = useState<PublicUnitDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [visitForm, setVisitForm] = useState({
    visitor_name: "",
    visitor_email: "",
    visitor_phone: "",
    preferred_date: "",
    message: "",
  });
  const [visitSuccess, setVisitSuccess] = useState(false);
  const [visitError, setVisitError] = useState<string | null>(null);
  const [visitLoading, setVisitLoading] = useState(false);

  useEffect(() => {
    if (!params.id) return;
    fetchPublicUnit(params.id)
      .then(setUnit)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Annonce introuvable"),
      );
  }, [params.id]);

  async function handleVisitRequest(e: React.FormEvent) {
    e.preventDefault();
    if (!unit) return;
    setVisitLoading(true);
    setVisitError(null);
    try {
      await createVisitRequest({
        unit_id: unit.id,
        visitor_name: visitForm.visitor_name,
        visitor_email: visitForm.visitor_email,
        visitor_phone: visitForm.visitor_phone,
        preferred_date: visitForm.preferred_date || undefined,
        message: visitForm.message || undefined,
      });
      setVisitSuccess(true);
      setVisitForm({
        visitor_name: "",
        visitor_email: "",
        visitor_phone: "",
        preferred_date: "",
        message: "",
      });
    } catch (err) {
      setVisitError(err instanceof ApiError ? err.message : "Demande impossible");
    } finally {
      setVisitLoading(false);
    }
  }

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-16">
      {!unit ? (
        <p className="text-center text-muted-foreground">{error ?? "Chargement…"}</p>
      ) : (
        <>
          <div>
            <p className="text-sm text-muted-foreground">{unit.code}</p>
            <h1 className="text-3xl font-bold">{UNIT_TYPE_LABELS[unit.type]}</h1>
            <p className="mt-2 text-muted-foreground">
              {unit.commune}
              {unit.quartier ? ` · ${unit.quartier}` : ""}
            </p>
          </div>

          <p className="text-2xl font-bold">{formatCurrency(unit.rent_amount)} / mois</p>

          {unit.description && (
            <p className="rounded-xl border border-border bg-card shadow-sm p-4 text-foreground">
              {unit.description}
            </p>
          )}

          {unit.photos.length > 0 && (
            <div className="grid gap-3 sm:grid-cols-2">
              {unit.photos.map((photo) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  key={photo.id}
                  src={`${API_URL}${photo.url}`}
                  alt={unit.code}
                  className="aspect-video rounded-lg object-cover"
                />
              ))}
            </div>
          )}

          <section className="rounded-xl border border-border bg-card shadow-sm p-6">
            <h2 className="text-xl font-bold">Demander une visite</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Remplissez le formulaire et nous vous recontacterons.
            </p>

            {visitSuccess && (
              <p className="mt-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
                Demande envoyée avec succès !
              </p>
            )}
            {visitError && <p className="mt-4 text-sm text-red-600">{visitError}</p>}

            <form onSubmit={handleVisitRequest} className="mt-4 space-y-3">
              <Input
                required
                placeholder="Nom complet"
                value={visitForm.visitor_name}
                onChange={(e) => setVisitForm({ ...visitForm, visitor_name: e.target.value })}
              />
              <Input
                required
                type="email"
                placeholder="Email"
                value={visitForm.visitor_email}
                onChange={(e) => setVisitForm({ ...visitForm, visitor_email: e.target.value })}
              />
              <Input
                required
                placeholder="Téléphone"
                value={visitForm.visitor_phone}
                onChange={(e) => setVisitForm({ ...visitForm, visitor_phone: e.target.value })}
              />
              <Input
                type="date"
                value={visitForm.preferred_date}
                onChange={(e) => setVisitForm({ ...visitForm, preferred_date: e.target.value })}
              />
              <textarea
                rows={3}
                placeholder="Message (optionnel)"
                className="w-full rounded-md border border-input px-3 py-2 text-sm"
                value={visitForm.message}
                onChange={(e) => setVisitForm({ ...visitForm, message: e.target.value })}
              />
              <Button type="submit" disabled={visitLoading}>
                {visitLoading ? "Envoi…" : "Envoyer la demande"}
              </Button>
            </form>
          </section>
        </>
      )}

      <Button asChild variant="outline" className="self-center">
        <Link href="/annonces">Retour aux annonces</Link>
      </Button>
    </main>
  );
}
