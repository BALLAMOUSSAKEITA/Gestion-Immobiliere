export const CURRENCY_CODE = "FG";

export function formatCurrency(value: string | number): string {
  const amount = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(amount)) return `— ${CURRENCY_CODE}`;
  return `${new Intl.NumberFormat("fr-GN", { maximumFractionDigits: 0 }).format(amount)} ${CURRENCY_CODE}`;
}
