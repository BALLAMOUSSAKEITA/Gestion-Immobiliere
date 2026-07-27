"use client";

import Link from "next/link";

import { RepairStatusBadge } from "@/components/repairs/repair-status-badge";
import { UrgencyBadge } from "@/components/repairs/urgency-badge";
import { type RepairStatus, type RepairSummary } from "@/lib/api";

const KANBAN_COLUMNS: { key: string; label: string; statuses: RepairStatus[] }[] = [
  { key: "new", label: "Nouvelles", statuses: ["new"] },
  { key: "review", label: "Analyse", statuses: ["under_review"] },
  { key: "active", label: "En cours", statuses: ["technician_assigned", "in_progress"] },
  { key: "done", label: "Terminées", statuses: ["completed"] },
  { key: "cancelled", label: "Annulées", statuses: ["cancelled"] },
];

type RepairKanbanProps = {
  items: RepairSummary[];
};

export function RepairKanban({ items }: RepairKanbanProps) {
  return (
    <div className="grid gap-4 overflow-x-auto lg:grid-cols-5">
      {KANBAN_COLUMNS.map((column) => {
        const columnItems = items.filter((item) => column.statuses.includes(item.status));
        return (
          <div key={column.key} className="min-w-[220px] rounded-xl border border-zinc-200 bg-zinc-50 p-3">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold">{column.label}</h3>
              <span className="rounded-full bg-white px-2 py-0.5 text-xs text-zinc-600">
                {columnItems.length}
              </span>
            </div>
            <div className="space-y-3">
              {columnItems.length === 0 ? (
                <p className="text-xs text-zinc-500">Aucune demande</p>
              ) : (
                columnItems.map((item) => (
                  <Link
                    key={item.id}
                    href={`/dashboard/reparations/${item.id}`}
                    className="block rounded-lg border border-zinc-200 bg-white p-3 shadow-sm transition hover:border-zinc-300"
                  >
                    <p className="font-medium text-sm">{item.title}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {item.unit_code} — {item.building_name}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-1">
                      <UrgencyBadge urgency={item.urgency} />
                      <RepairStatusBadge status={item.status} />
                    </div>
                  </Link>
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
