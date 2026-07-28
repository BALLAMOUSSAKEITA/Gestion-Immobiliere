"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { ExpenseForm } from "@/components/expenses/expense-form";
import { AppHeader } from "@/components/layout/app-header";
import {
  ApiError,
  createExpense,
  fetchBuildings,
  fetchExpenseCategories,
  type ExpenseCategory,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function NewExpensePage() {
  const router = useRouter();
  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  const [buildings, setBuildings] = useState<{ id: string; label: string }[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    Promise.all([
      fetchExpenseCategories(token),
      fetchBuildings(token, { page_size: 100 }),
    ])
      .then(([cats, bldgs]) => {
        setCategories(cats);
        setBuildings(bldgs.items.map((b) => ({ id: b.id, label: `${b.code} — ${b.name}` })));
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Nouvelle dépense</h1>
          <p className="mt-2 text-muted-foreground">
            Les dépenses ≥ 500 000 FCFA nécessitent une validation du super administrateur.
          </p>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {categories.length > 0 && buildings.length > 0 && (
          <ExpenseForm
            categories={categories}
            buildings={buildings}
            onSubmit={async (values) => {
              const token = getAccessToken();
              if (!token) return;
              const expense = await createExpense(token, values);
              router.push(`/dashboard/depenses/${expense.id}`);
            }}
          />
        )}
      </main>
    </ProtectedRoute>
  );
}
