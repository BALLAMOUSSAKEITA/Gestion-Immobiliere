"use client";

import { FileText, Upload, X } from "lucide-react";
import { useId, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type FileInputProps = {
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  required?: boolean;
  hint?: string;
  label?: string;
  className?: string;
  value?: File | File[] | null;
  onChange?: (files: File[]) => void;
};

function formatBytes(size: number): string {
  if (size < 1024) return `${size} o`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} Ko`;
  return `${(size / (1024 * 1024)).toFixed(1)} Mo`;
}

export function FileInput({
  accept,
  multiple = false,
  disabled = false,
  required = false,
  hint = "PDF, images ou documents — max. 10 Mo",
  label = "Choisir un fichier",
  className,
  value,
  onChange,
}: FileInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();
  const [dragOver, setDragOver] = useState(false);
  const [internalFiles, setInternalFiles] = useState<File[]>([]);

  const controlled =
    value !== undefined
      ? Array.isArray(value)
        ? value
        : value
          ? [value]
          : []
      : null;
  const files = controlled ?? internalFiles;

  const applyFiles = (next: File[]) => {
    const selected = multiple ? next : next.slice(0, 1);
    if (controlled === null) setInternalFiles(selected);
    onChange?.(selected);
  };

  const clearFiles = () => {
    if (controlled === null) setInternalFiles([]);
    onChange?.([]);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className={cn("space-y-2", className)}>
      <label
        htmlFor={inputId}
        onDragEnter={(e) => {
          e.preventDefault();
          if (!disabled) setDragOver(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragOver(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragOver(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (disabled) return;
          const dropped = Array.from(e.dataTransfer.files ?? []);
          if (dropped.length) applyFiles(dropped);
        }}
        className={cn(
          "group relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-5 py-8 text-center transition-all",
          disabled
            ? "cursor-not-allowed border-border bg-muted/30 opacity-60"
            : dragOver
              ? "border-primary bg-primary/10"
              : "border-border bg-muted/20 hover:border-primary/50 hover:bg-primary/5",
        )}
      >
        <div
          className={cn(
            "flex h-12 w-12 items-center justify-center rounded-full border border-border bg-background shadow-sm transition-transform",
            !disabled && "group-hover:scale-105",
          )}
        >
          <Upload className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">{label}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            ou glissez-déposez ici
          </p>
          {hint && (
            <p className="mt-2 text-xs text-muted-foreground">{hint}</p>
          )}
        </div>
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          required={required && files.length === 0}
          onChange={(e) => {
            const selected = Array.from(e.target.files ?? []);
            if (selected.length) applyFiles(selected);
          }}
          className="sr-only"
        />
      </label>

      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((file) => (
            <li
              key={`${file.name}-${file.size}-${file.lastModified}`}
              className="flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                <FileText className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
              </div>
              {!disabled && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 shrink-0 p-0"
                  onClick={clearFiles}
                  aria-label="Retirer le fichier"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
