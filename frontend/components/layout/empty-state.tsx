import { Button } from "@/components/ui/button";

type EmptyStateProps = {
  title: string;
  description?: string;
  actionLabel?: string;
  actionHref?: string;
};

export function EmptyState({ title, description, actionLabel, actionHref }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-[12px] bg-[var(--deco)] px-6 py-16 text-center">
      <h3 className="text-sm font-medium text-foreground">{title}</h3>
      {description && <p className="mt-2 max-w-md text-sm text-muted-foreground">{description}</p>}
      {actionLabel && actionHref && (
        <Button asChild className="mt-6" variant="outline">
          <a href={actionHref}>{actionLabel}</a>
        </Button>
      )}
    </div>
  );
}
