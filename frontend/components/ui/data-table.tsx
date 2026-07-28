import { cn } from "@/lib/utils";

type DataTableProps = {
  children: React.ReactNode;
  className?: string;
  empty?: React.ReactNode;
};

export function DataTable({ children, className, empty }: DataTableProps) {
  return (
    <div className={cn("table-shell overflow-hidden rounded-xl border border-border bg-card shadow-sm", className)}>
      <div className="table-scroll -mx-px overflow-x-auto overscroll-x-contain">
        {children}
      </div>
      {empty}
    </div>
  );
}
