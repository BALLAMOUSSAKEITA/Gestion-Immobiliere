"use client";

import Link from "next/link";
import { useState } from "react";

import { PublicHeader } from "@/components/layout/public-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, createPublicContact } from "@/lib/api";

export default function ContactPage() {
  const [form, setForm] = useState({
    sender_name: "",
    sender_email: "",
    sender_phone: "",
    subject: "",
    body: "",
  });
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await createPublicContact({
        sender_name: form.sender_name,
        sender_email: form.sender_email,
        sender_phone: form.sender_phone || undefined,
        subject: form.subject,
        body: form.body,
      });
      setSuccess(true);
      setForm({
        sender_name: "",
        sender_email: "",
        sender_phone: "",
        subject: "",
        body: "",
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Envoi impossible");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PublicHeader />
      <main className="mx-auto flex max-w-xl flex-col gap-6 px-6 py-16">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Contact</h1>
          <p className="mt-2 text-zinc-600">
            Une question ? Écrivez-nous, nous vous répondrons rapidement.
          </p>
        </div>

        {success && (
          <p className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
            Message envoyé avec succès. Merci !
          </p>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-zinc-200 bg-white p-6">
          <div>
            <label className="mb-1 block text-sm font-medium">Nom</label>
            <Input
              required
              value={form.sender_name}
              onChange={(e) => setForm({ ...form, sender_name: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Email</label>
            <Input
              required
              type="email"
              value={form.sender_email}
              onChange={(e) => setForm({ ...form, sender_email: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Téléphone</label>
            <Input
              value={form.sender_phone}
              onChange={(e) => setForm({ ...form, sender_phone: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Sujet</label>
            <Input
              required
              value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Message</label>
            <textarea
              required
              rows={5}
              className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
              value={form.body}
              onChange={(e) => setForm({ ...form, body: e.target.value })}
            />
          </div>
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Envoi…" : "Envoyer"}
          </Button>
        </form>

        <Button asChild variant="outline" className="self-center">
          <Link href="/annonces">Retour aux annonces</Link>
        </Button>
      </main>
    </>
  );
}
