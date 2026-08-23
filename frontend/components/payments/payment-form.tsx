"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  fetchLeasePeriods,
  formatCurrency,
  PAYMENT_METHOD_LABELS,
  type LeaseSummary,
  type PaymentCreatePayload,
  type PaymentMethod,
  type RentPeriod,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

const MONTHS_FR = [
  "janvier",
  "février",
  "mars",
  "avril",
  "mai",
  "juin",
  "juillet",
  "août",
  "septembre",
  "octobre",
  "novembre",
  "décembre",
];

type PaymentFormProps = {
  leases: LeaseSummary[];
  onSubmit: (values: PaymentCreatePayload) => Promise<void>;
};

type BreakdownRow = {
  year: number;
  month: number;
  remaining: number;
};

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

function firstDayOfMonth(year: number, month: number): string {
  return `${year}-${pad2(month)}-01`;
}

function lastDayOfMonth(year: number, month: number): string {
  const day = new Date(year, month, 0).getDate();
  return `${year}-${pad2(month)}-${pad2(day)}`;
}

function addMonths(year: number, month: number, extra: number): { year: number; month: number } {
  const index = year * 12 + (month - 1) + extra;
  return { year: Math.floor(index / 12), month: (index % 12) + 1 };
}

function monthsInRange(from: string, to: string): { year: number; month: number }[] {
  const start = new Date(`${from}T00:00:00`);
  const end = new Date(`${to}T00:00:00`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || start > end) {
    return [];
  }
  const items: { year: number; month: number }[] = [];
  let year = start.getFullYear();
  let month = start.getMonth() + 1;
  const endYear = end.getFullYear();
  const endMonth = end.getMonth() + 1;
  while (year < endYear || (year === endYear && month <= endMonth)) {
    items.push({ year, month });
    ({ year, month } = addMonths(year, month, 1));
  }
  return items;
}

function formatMonthLabel(year: number, month: number): string {
  return `${MONTHS_FR[month - 1] ?? month} ${year}`;
}

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

export function PaymentForm({ leases, onSubmit }: PaymentFormProps) {
  const [leaseId, setLeaseId] = useState("");
  const [periods, setPeriods] = useState<RentPeriod[]>([]);
  const [periodsLoading, setPeriodsLoading] = useState(false);
  const [coveredFrom, setCoveredFrom] = useState("");
  const [coveredTo, setCoveredTo] = useState("");
  const [form, setForm] = useState({
    amount: "",
    payment_method: "cash" as PaymentMethod,
    payment_date: new Date().toISOString().slice(0, 10),
    reference: "",
    notes: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedLease = leases.find((lease) => lease.id === leaseId);

  useEffect(() => {
    if (!leaseId) {
      setPeriods([]);
      setCoveredFrom("");
      setCoveredTo("");
      setForm((current) => ({ ...current, amount: "" }));
      return;
    }
    const token = getAccessToken();
    if (!token) return;
    let cancelled = false;
    setPeriods([]);
    setCoveredFrom("");
    setCoveredTo("");
    setForm((current) => ({ ...current, amount: "" }));
    setPeriodsLoading(true);
    fetchLeasePeriods(token, leaseId)
      .then((items) => {
        if (cancelled) return;
        setPeriods(items);
        const firstUnpaid = items.find((item) => Number(item.remaining_amount) > 0);
        if (firstUnpaid) {
          setCoveredFrom(firstDayOfMonth(firstUnpaid.period_year, firstUnpaid.period_month));
          setCoveredTo(lastDayOfMonth(firstUnpaid.period_year, firstUnpaid.period_month));
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Impossible de charger les échéances");
        }
      })
      .finally(() => {
        if (!cancelled) setPeriodsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [leaseId]);

  const breakdown = useMemo<BreakdownRow[]>(() => {
    if (!coveredFrom || !coveredTo || !selectedLease) return [];
    const rent = Number(selectedLease.rent_amount);
    const start = new Date(`${selectedLease.start_date}T00:00:00`);
    const startKey = start.getFullYear() * 12 + start.getMonth();
    const endKey = selectedLease.end_date
      ? (() => {
          const end = new Date(`${selectedLease.end_date}T00:00:00`);
          return end.getFullYear() * 12 + end.getMonth();
        })()
      : null;
    return monthsInRange(coveredFrom, coveredTo)
      .filter(({ year, month }) => {
        const key = year * 12 + (month - 1);
        if (key < startKey) return false;
        if (endKey !== null && key > endKey) return false;
        return true;
      })
      .map(({ year, month }) => {
      const period = periods.find(
        (item) => item.period_year === year && item.period_month === month,
      );
      if (!period) {
        return {
          year,
          month,
          remaining: Number.isFinite(rent) ? rent : 0,
        };
      }
      return {
        year,
        month,
        remaining: Math.max(0, Number(period.remaining_amount)),
      };
    });
  }, [coveredFrom, coveredTo, periods, selectedLease]);

  const dueOnPeriod = useMemo(
    () => roundMoney(breakdown.reduce((sum, row) => sum + row.remaining, 0)),
    [breakdown],
  );
  const coveredMonthCount = breakdown.filter((row) => row.remaining > 0).length;

  useEffect(() => {
    if (!coveredFrom || !coveredTo) return;
    setForm((current) => ({
      ...current,
      amount: dueOnPeriod > 0 ? dueOnPeriod.toFixed(2) : "",
    }));
  }, [coveredFrom, coveredTo, dueOnPeriod]);

  const applyPreset = (monthCount: number) => {
    if (!coveredFrom) return;
    const start = new Date(`${coveredFrom}T00:00:00`);
    if (Number.isNaN(start.getTime())) return;
    const startYear = start.getFullYear();
    const startMonth = start.getMonth() + 1;
    const end = addMonths(startYear, startMonth, monthCount - 1);
    setCoveredFrom(firstDayOfMonth(startYear, startMonth));
    setCoveredTo(lastDayOfMonth(end.year, end.month));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (!coveredFrom || !coveredTo) {
        throw new Error("Choisissez la période couverte par ce paiement");
      }
      if (breakdown.length === 0) {
        throw new Error("Aucune échéance de loyer sur la période sélectionnée");
      }
      if (dueOnPeriod <= 0) {
        throw new Error("Cette période est déjà soldée");
      }
      const amount = Number(form.amount);
      if (!Number.isFinite(amount) || amount <= 0) {
        throw new Error("Montant invalide");
      }
      if (amount > dueOnPeriod) {
        throw new Error("Le montant dépasse le reste dû sur la période sélectionnée");
      }
      await onSubmit({
        lease_id: leaseId,
        amount: amount.toFixed(2),
        payment_method: form.payment_method,
        payment_date: form.payment_date,
        covered_from: coveredFrom,
        covered_to: coveredTo,
        reference: form.reference || undefined,
        notes: form.notes || undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="grid gap-4 rounded-xl border border-border bg-card shadow-sm p-6"
    >
      <div>
        <label htmlFor="lease_id" className="mb-1 block text-sm text-muted-foreground">
          Bail
        </label>
        <select
          id="lease_id"
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={leaseId}
          onChange={(e) => setLeaseId(e.target.value)}
          required
        >
          <option value="">Sélectionner un bail actif</option>
          {leases.map((lease) => (
            <option key={lease.id} value={lease.id}>
              {lease.tenant_name} — {lease.unit_code} ({formatCurrency(lease.rent_amount)}
              /mois)
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-3 rounded-lg border border-border bg-muted/30 p-4">
        <div>
          <p className="text-sm font-medium">Période couverte par ce paiement</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Indiquez les dates du loyer réglé, par exemple du 1 janvier au 31 mars. Le montant
            est calculé automatiquement.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="covered_from" className="mb-1 block text-sm text-muted-foreground">
              Du
            </label>
            <Input
              id="covered_from"
              type="date"
              value={coveredFrom}
              min={selectedLease?.start_date}
              max={selectedLease?.end_date ?? undefined}
              onChange={(e) => setCoveredFrom(e.target.value)}
              required
              disabled={!leaseId}
            />
          </div>
          <div>
            <label htmlFor="covered_to" className="mb-1 block text-sm text-muted-foreground">
              Au
            </label>
            <Input
              id="covered_to"
              type="date"
              value={coveredTo}
              min={coveredFrom || selectedLease?.start_date}
              max={selectedLease?.end_date ?? undefined}
              onChange={(e) => setCoveredTo(e.target.value)}
              required
              disabled={!leaseId}
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {[1, 3, 6].map((count) => (
            <Button
              key={count}
              type="button"
              variant="outline"
              size="sm"
              disabled={!coveredFrom}
              onClick={() => applyPreset(count)}
            >
              {count} mois
            </Button>
          ))}
        </div>

        {periodsLoading && (
          <p className="text-sm text-muted-foreground">Chargement des échéances…</p>
        )}

        {breakdown.length > 0 && (
          <div className="rounded-md border border-border bg-card p-3">
            <p className="text-sm font-medium">Récapitulatif</p>
            <ul className="mt-2 space-y-1 text-sm">
              {breakdown.map((row) => (
                <li
                  key={`${row.year}-${row.month}`}
                  className="flex items-center justify-between gap-3"
                >
                  <span className="capitalize">{formatMonthLabel(row.year, row.month)}</span>
                  <span
                    className={
                      row.remaining <= 0 ? "text-muted-foreground line-through" : "font-medium"
                    }
                  >
                    {row.remaining <= 0
                      ? "Déjà soldé"
                      : formatCurrency(row.remaining.toFixed(2))}
                  </span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-sm font-semibold">
              {coveredMonthCount} mois à régler — total {formatCurrency(dueOnPeriod.toFixed(2))}
            </p>
          </div>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="amount" className="mb-1 block text-sm text-muted-foreground">
            Montant (FG)
          </label>
          <Input
            id="amount"
            placeholder="Montant calculé"
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
            required
          />
          <p className="mt-1 text-xs text-muted-foreground">
            Calculé selon la période. Vous pouvez le réduire pour un paiement partiel.
          </p>
        </div>
        <div>
          <label htmlFor="payment_method" className="mb-1 block text-sm text-muted-foreground">
            Mode de paiement
          </label>
          <select
            id="payment_method"
            className="w-full rounded-md border border-border px-3 py-2 text-sm"
            value={form.payment_method}
            onChange={(e) =>
              setForm({ ...form, payment_method: e.target.value as PaymentMethod })
            }
          >
            {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="payment_date" className="mb-1 block text-sm text-muted-foreground">
            Date de paiement
          </label>
          <Input
            id="payment_date"
            type="date"
            value={form.payment_date}
            onChange={(e) => setForm({ ...form, payment_date: e.target.value })}
            required
          />
        </div>
        <div>
          <label htmlFor="reference" className="mb-1 block text-sm text-muted-foreground">
            Référence transaction
          </label>
          <Input
            id="reference"
            placeholder="Optionnel"
            value={form.reference}
            onChange={(e) => setForm({ ...form, reference: e.target.value })}
          />
        </div>
      </div>
      <div>
        <label htmlFor="notes" className="mb-1 block text-sm text-muted-foreground">
          Notes
        </label>
        <Input
          id="notes"
          placeholder="Optionnel"
          value={form.notes}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
        />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Button type="submit" disabled={loading || !leaseId}>
        {loading ? "Enregistrement…" : "Enregistrer et générer le reçu"}
      </Button>
    </form>
  );
}
