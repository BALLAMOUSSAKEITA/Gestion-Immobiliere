"use client";

import { ImagePlus, Upload } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";

type ImageUploadFieldProps = {
  label: string;
  hint?: string;
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  embedded?: boolean;
  /** Sélection seule — pas de bouton d'envoi (ex. formulaire de création) */
  selectOnly?: boolean;
  onFileSelect?: (files: File[]) => void;
  onUpload?: (files: File[]) => Promise<void>;
};

export function ImageUploadField({
  label,
  hint = "JPG, PNG ou WebP — max. 10 Mo",
  accept = "image/jpeg,image/png,image/webp,image/gif",
  multiple = false,
  disabled = false,
  embedded = false,
  selectOnly = false,
  onFileSelect,
  onUpload,
}: ImageUploadFieldProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const applyFiles = (selected: File[]) => {
    if (!selected.length) return;
    setError(null);
    setFiles(selected);
    setPreviews(selected.map((file) => URL.createObjectURL(file)));
    onFileSelect?.(selected);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    applyFiles(Array.from(event.target.files ?? []));
  };

  const handleUpload = async () => {
    if (!files.length) {
      setError("Sélectionnez un fichier image.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await onUpload?.(files);
      setFiles([]);
      setPreviews([]);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Envoi impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={embedded ? "" : "rounded-xl border border-border bg-card p-5 shadow-sm"}>
      <div className={embedded ? "mb-3" : "mb-3"}>
        <h2 className={embedded ? "text-base font-semibold" : "text-lg font-semibold"}>{label}</h2>
        {hint && <p className="mt-1 text-sm text-muted-foreground">{hint}</p>}
      </div>

      <label
        htmlFor={`image-upload-${label}`}
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
          applyFiles(Array.from(e.dataTransfer.files ?? []));
        }}
        className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-10 transition-colors ${
          disabled
            ? "cursor-not-allowed border-border bg-muted/30 opacity-60"
            : dragOver
              ? "border-primary bg-primary/15"
              : "border-primary/40 bg-primary/5 hover:border-primary hover:bg-primary/10"
        }`}
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-background shadow-sm">
          <ImagePlus className="h-7 w-7 text-primary" />
        </div>
        <div className="text-center">
          <p className="font-medium text-foreground">
            Cliquez pour choisir {multiple ? "des images" : "une image"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">ou glissez-déposez ici</p>
        </div>
        <input
          ref={inputRef}
          id={`image-upload-${label}`}
          type="file"
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          onChange={handleFileChange}
          className="sr-only"
        />
      </label>

      {files.length > 0 && (
        <div className="mt-4 space-y-3">
          <p className="text-sm font-medium">
            {files.length} fichier{files.length > 1 ? "s" : ""} sélectionné{files.length > 1 ? "s" : ""}
          </p>
          <div className="flex flex-wrap gap-3">
            {previews.map((preview, index) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={preview}
                src={preview}
                alt={files[index]?.name ?? "Aperçu"}
                className="h-24 w-24 rounded-lg border border-border object-cover"
              />
            ))}
          </div>
          {selectOnly ? (
            <p className="text-sm text-emerald-700">
              Photo prête — elle sera enregistrée à la création de l&apos;immeuble.
            </p>
          ) : (
            <Button type="button" onClick={handleUpload} disabled={loading || disabled}>
              <Upload className="mr-2 h-4 w-4" />
              {loading ? "Envoi en cours…" : "Envoyer la photo"}
            </Button>
          )}
        </div>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
    </div>
  );
}
