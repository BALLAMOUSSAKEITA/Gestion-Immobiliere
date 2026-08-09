"use client";

import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { Button } from "@/components/ui/button";

export type ConfirmOptions = {
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "default" | "destructive";
};

type ConfirmState = ConfirmOptions & { open: true };

type ConfirmContextValue = {
  confirm: (options: ConfirmOptions) => Promise<boolean>;
};

const ConfirmContext = createContext<ConfirmContextValue | null>(null);

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ConfirmState | null>(null);
  const resolveRef = useRef<((value: boolean) => void) | null>(null);

  const confirm = useCallback((options: ConfirmOptions) => {
    return new Promise<boolean>((resolve) => {
      resolveRef.current = resolve;
      setState({ ...options, open: true });
    });
  }, []);

  const close = (result: boolean) => {
    resolveRef.current?.(result);
    resolveRef.current = null;
    setState(null);
  };

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      {state && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="confirm-dialog-title"
            className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-[var(--shadow-dropdown)]"
          >
            <h2 id="confirm-dialog-title" className="text-lg font-semibold">
              {state.title}
            </h2>
            {state.description && (
              <p className="mt-2 text-sm text-muted-foreground">{state.description}</p>
            )}
            <div className="mt-6 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => close(false)}>
                {state.cancelLabel ?? "Annuler"}
              </Button>
              <Button
                type="button"
                variant={state.variant === "destructive" ? "destructive" : "default"}
                onClick={() => close(true)}
              >
                {state.confirmLabel ?? "Confirmer"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const context = useContext(ConfirmContext);
  if (!context) {
    throw new Error("useConfirm must be used within ConfirmProvider");
  }
  return context.confirm;
}
