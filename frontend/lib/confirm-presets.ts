import type { ConfirmOptions } from "@/contexts/confirm-context";

export function deleteConfirm(entity: string): ConfirmOptions {
  return {
    title: `Supprimer ${entity} ?`,
    description: "Cette action est irréversible.",
    confirmLabel: "Supprimer",
    variant: "destructive",
  };
}

export function modifyConfirm(description: string, confirmLabel = "Confirmer"): ConfirmOptions {
  return {
    title: "Confirmer la modification",
    description,
    confirmLabel,
  };
}
