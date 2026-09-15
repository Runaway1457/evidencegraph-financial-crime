import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock


class FileSystemObjectStore:
    """Atomic local object store for the standalone profile."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        target = (self._root / key).resolve()
        if self._root not in target.parents:
            raise ValueError("object key escapes the configured storage root")
        return target

    def put(self, key: str, content: bytes) -> None:
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        try:
            os.replace(temporary_path, target)
        finally:
            temporary_path.unlink(missing_ok=True)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


class InMemoryObjectStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self._lock = RLock()

    def put(self, key: str, content: bytes) -> None:
        with self._lock:
            self.objects[key] = bytes(content)

    def delete(self, key: str) -> None:
        with self._lock:
            self.objects.pop(key, None)
