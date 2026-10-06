"use client";

import { useState } from "react";
import { Copy, Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";

type PasswordRevealProps = {
  password?: string | null;
  emptyLabel?: string;
  defaultVisible?: boolean;
};

export function PasswordReveal({
  password,
  emptyLabel = "Non disponible",
  defaultVisible = false,
}: PasswordRevealProps) {
  const [visible, setVisible] = useState(defaultVisible);
  const [copied, setCopied] = useState(false);

  if (!password) {
    return (
      <span className="block text-sm leading-snug text-muted-foreground">{emptyLabel}</span>
    );
  }

  const copyPassword = async () => {
    try {
      await navigator.clipboard.writeText(password);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="flex max-w-full flex-wrap items-center gap-1">
      <code className="max-w-full break-all rounded-md bg-muted px-2 py-1 font-mono text-xs">
        {visible ? password : "••••••••"}
      </code>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => setVisible((current) => !current)}
        aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={copyPassword}
        aria-label="Copier le mot de passe"
      >
        <Copy className="h-4 w-4" />
      </Button>
      {copied && <span className="text-xs text-emerald-700">Copié</span>}
    </div>
  );
}
