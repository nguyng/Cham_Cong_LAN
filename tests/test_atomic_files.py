import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from client.app.files import write_bytes_atomic, write_text_atomic


@pytest.fixture
def runtime_dir():
    directory = Path(".test-runtime") / "atomic-files" / str(uuid4())
    directory.mkdir(parents=True)
    yield directory
    shutil.rmtree(directory, ignore_errors=True)


def test_atomic_file_write_replaces_complete_content(runtime_dir):
    destination = runtime_dir / "report.xlsx"
    destination.write_bytes(b"old")

    write_bytes_atomic(destination, b"complete-new-content")

    assert destination.read_bytes() == b"complete-new-content"
    assert list(runtime_dir.glob("*.tmp")) == []


def test_atomic_file_write_preserves_old_file_when_replace_fails(runtime_dir, monkeypatch):
    destination = runtime_dir / "config.json"
    destination.write_text("old", encoding="utf-8")

    def fail_replace(_source, _destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        write_text_atomic(destination, "new")

    assert destination.read_text(encoding="utf-8") == "old"
    assert list(runtime_dir.glob("*.tmp")) == []
