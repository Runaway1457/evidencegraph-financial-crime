from pathlib import Path

import pytest

from evidencegraph.infrastructure.object_store import FileSystemObjectStore


def test_filesystem_object_store_writes_atomically_and_deletes(tmp_path: Path) -> None:
    store = FileSystemObjectStore(tmp_path)
    store.put("case_1/object_1", b"evidence")
    target = tmp_path / "case_1" / "object_1"
    assert target.read_bytes() == b"evidence"

    store.delete("case_1/object_1")
    assert not target.exists()


def test_filesystem_object_store_rejects_path_escape(tmp_path: Path) -> None:
    store = FileSystemObjectStore(tmp_path)
    with pytest.raises(ValueError, match="escapes"):
        store.put("../outside", b"forbidden")
