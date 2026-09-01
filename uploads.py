"""Almacenamiento seguro de imágenes administradas por New Records."""

from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.datastructures import FileStorage


def _detectar_extension(contenido: bytes) -> str | None:
    """Reconoce los formatos permitidos por su firma binaria, no por el nombre."""
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if contenido.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if contenido.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if (
        len(contenido) >= 12
        and contenido.startswith(b"RIFF")
        and contenido[8:12] == b"WEBP"
    ):
        return ".webp"
    return None


def guardar_imagen_subida(archivo: FileStorage | None, subcarpeta: str) -> str | None:
    """Valida, guarda y retorna una ruta relativa servible por Flask."""
    if archivo is None or not archivo.filename:
        return None
    if subcarpeta not in {"productos", "categorias"}:
        raise ValueError("La ubicación de la imagen no es válida.")

    limite = int(current_app.config["MAX_IMAGE_UPLOAD_BYTES"])
    contenido = archivo.stream.read(limite + 1)
    if not contenido:
        raise ValueError("La imagen seleccionada está vacía.")
    if len(contenido) > limite:
        raise ValueError("La imagen no puede superar los 5 MB.")

    extension = _detectar_extension(contenido)
    if extension is None:
        raise ValueError("La portada debe ser una imagen PNG, JPG, WEBP o GIF válida.")

    raiz_estatica = Path(current_app.static_folder).resolve()
    raiz_uploads = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    destino_carpeta = (raiz_uploads / subcarpeta).resolve()
    if raiz_estatica not in destino_carpeta.parents:
        raise RuntimeError("La carpeta de portadas debe permanecer dentro de static.")

    destino_carpeta.mkdir(parents=True, exist_ok=True)
    destino = destino_carpeta / f"{uuid4().hex}{extension}"
    destino.write_bytes(contenido)
    return destino.relative_to(raiz_estatica).as_posix()


def eliminar_imagen_gestionada(ruta_relativa: str | None) -> None:
    """Elimina solamente archivos creados dentro de static/img/uploads."""
    if not ruta_relativa or not ruta_relativa.startswith("img/uploads/"):
        return

    raiz_estatica = Path(current_app.static_folder).resolve()
    raiz_uploads = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    destino = (raiz_estatica / ruta_relativa).resolve()
    if raiz_uploads not in destino.parents:
        return
    destino.unlink(missing_ok=True)
