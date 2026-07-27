import mimetypes
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.config import get_settings
from app.models.enums import EntityType

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm"}
MIME_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
}


class StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self.upload_dir = Path(settings.upload_dir)
        self.max_size = settings.document_max_size_bytes

    def save_upload(
        self,
        file: UploadFile,
        entity_type: EntityType,
        entity_id: str,
    ) -> tuple[str, str, int, str]:
        extension = Path(file.filename or "file.bin").suffix.lower() or ".bin"
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")

        content = file.file.read()
        file_size = len(content)
        if file_size > self.max_size:
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10 Mo)")

        safe_name = Path(file.filename or "document").name.replace(" ", "_")
        filename = f"{uuid4()}_{safe_name}"
        target_dir = self.upload_dir / entity_type.value / entity_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        with target_path.open("wb") as buffer:
            buffer.write(content)

        mime_type = MIME_BY_EXTENSION.get(extension) or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        file_url = f"/uploads/{entity_type.value}/{entity_id}/{filename}"
        return file_url, safe_name, file_size, mime_type

    def resolve_path(self, file_url: str) -> Path:
        if not file_url.startswith("/uploads/"):
            raise HTTPException(status_code=404, detail="Fichier introuvable")
        relative = file_url.removeprefix("/uploads/")
        path = self.upload_dir / relative
        if not path.exists():
            raise HTTPException(status_code=404, detail="Fichier introuvable")
        return path

    def delete_file(self, file_url: str) -> None:
        try:
            path = self.resolve_path(file_url)
            path.unlink(missing_ok=True)
        except HTTPException:
            pass
