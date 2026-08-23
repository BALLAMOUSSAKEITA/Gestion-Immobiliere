export const CURRENCY_CODE = "FG";

export function formatCurrency(value: string | number): string {
  const amount = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(amount)) return `— ${CURRENCY_CODE}`;
  return `${new Intl.NumberFormat("fr-GN", { maximumFractionDigits: 0 }).format(amount)} ${CURRENCY_CODE}`;
}

export function formatCoveredPeriod(
  from: string | null | undefined,
  to: string | null | undefined,
): string | null {
  if (!from || !to) return null;
  const start = new Date(`${from}T00:00:00`);
  const end = new Date(`${to}T00:00:00`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  return `${start.toLocaleDateString("fr-FR")} – ${end.toLocaleDateString("fr-FR")}`;
}
