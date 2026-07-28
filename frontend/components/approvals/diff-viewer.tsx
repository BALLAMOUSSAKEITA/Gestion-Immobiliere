"use client";

type DiffViewerProps = {
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
};

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

export function DiffViewer({ before, after }: DiffViewerProps) {
  const keys = Array.from(
    new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})]),
  );

  if (keys.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Aucune donnée de comparaison disponible.</p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-border bg-muted/50">
          <tr>
            <th className="px-4 py-3">Champ</th>
            <th className="px-4 py-3">Avant</th>
            <th className="px-4 py-3">Après</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => {
            const oldVal = before?.[key];
            const newVal = after?.[key];
            const changed = JSON.stringify(oldVal) !== JSON.stringify(newVal);
            return (
              <tr key={key} className="border-b border-border">
                <td className="px-4 py-3 font-medium">{key}</td>
                <td className="px-4 py-3 text-muted-foreground">{formatValue(oldVal)}</td>
                <td
                  className={`px-4 py-3 ${changed ? "bg-amber-50 font-medium text-amber-900" : "text-muted-foreground"}`}
                >
                  {formatValue(newVal)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
