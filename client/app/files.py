import os
import uuid
from pathlib import Path


def write_bytes_atomic(path: str | Path, content: bytes):
    """Replace a file only after the complete payload is safely written."""
    destination = Path(path)
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def write_text_atomic(path: str | Path, content: str, *, encoding: str = "utf-8"):
    write_bytes_atomic(path, content.encode(encoding))
