"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AppHeader } from "@/components/layout/app-header";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { RoleBadge } from "@/components/auth/role-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/auth-context";
import { ApiError } from "@/lib/api";

const passwordSchema = z
  .object({
    current_password: z.string().min(8),
    new_password: z
      .string()
      .min(8)
      .regex(/[A-Z]/, "Au moins une majuscule")
      .regex(/\d/, "Au moins un chiffre"),
    confirm_password: z.string().min(8),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Les mots de passe ne correspondent pas",
    path: ["confirm_password"],
  });

type PasswordFormValues = z.infer<typeof passwordSchema>;

function ProfilContent() {
  const { user, changePassword } = useAuth();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
  });

  if (!user) return null;

  const onSubmit = handleSubmit(async (values) => {
    setMessage(null);
    setError(null);
    try {
      await changePassword(values.current_password, values.new_password);
      setMessage("Mot de passe modifié. Veuillez vous reconnecter.");
      reset();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Impossible de modifier le mot de passe");
      }
    }
  });

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-8 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Mon profil</h1>
        <p className="mt-2 text-zinc-600">Informations de votre compte.</p>
      </div>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-zinc-500">Nom complet</dt>
            <dd className="font-medium">
              {user.first_name} {user.last_name}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-500">Email</dt>
            <dd className="font-medium">{user.email}</dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-500">Téléphone</dt>
            <dd className="font-medium">{user.phone ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-500">Rôle</dt>
            <dd className="mt-1">
              <RoleBadge code={user.role.code} label={user.role.label} />
            </dd>
          </div>
        </dl>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Changer le mot de passe</h2>
        <form onSubmit={onSubmit} className="mt-4 space-y-4">
          <div>
            <label className="text-sm font-medium">Mot de passe actuel</label>
            <Input type="password" {...register("current_password")} />
            {errors.current_password && (
              <p className="text-sm text-red-600">
                {errors.current_password.message}
              </p>
            )}
          </div>
          <div>
            <label className="text-sm font-medium">Nouveau mot de passe</label>
            <Input type="password" {...register("new_password")} />
            {errors.new_password && (
              <p className="text-sm text-red-600">{errors.new_password.message}</p>
            )}
          </div>
          <div>
            <label className="text-sm font-medium">Confirmer le mot de passe</label>
            <Input type="password" {...register("confirm_password")} />
            {errors.confirm_password && (
              <p className="text-sm text-red-600">
                {errors.confirm_password.message}
              </p>
            )}
          </div>

          {message && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {message}
            </div>
          )}
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Enregistrement..." : "Mettre à jour"}
          </Button>
        </form>
      </section>
    </main>
  );
}

export default function ProfilPage() {
  return (
    <ProtectedRoute>
      <AppHeader />
      <ProfilContent />
    </ProtectedRoute>
  );
}
