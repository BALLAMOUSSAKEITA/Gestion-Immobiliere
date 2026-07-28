"use client";

import { useState } from "react";
import { Mail } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
      setForm({ sender_name: "", sender_email: "", sender_phone: "", subject: "", body: "" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Envoi impossible");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-container">
      <PageHeader
        title="Contact"
        description="Une question sur un logement ou nos services ? Écrivez-nous."
      />

      <div className="mx-auto max-w-xl">
        {success && (
          <Alert variant="success" className="mb-6">
            Message envoyé avec succès. Nous vous répondrons rapidement.
          </Alert>
        )}
        {error && <Alert variant="destructive" className="mb-6">{error}</Alert>}

        <Card>
          <CardContent className="p-6">
            <div className="mb-6 flex items-center gap-3 text-primary">
              <Mail className="h-5 w-5" />
              <p className="font-medium">Formulaire de contact</p>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Nom</Label>
                <Input required value={form.sender_name} onChange={(e) => setForm({ ...form, sender_name: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input required type="email" value={form.sender_email} onChange={(e) => setForm({ ...form, sender_email: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Téléphone</Label>
                <Input value={form.sender_phone} onChange={(e) => setForm({ ...form, sender_phone: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Sujet</Label>
                <Input required value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Message</Label>
                <Textarea required rows={5} value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} />
              </div>
              <Button type="submit" disabled={loading} variant="accent" className="w-full">
                {loading ? "Envoi…" : "Envoyer le message"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
