import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

spec = importlib.util.spec_from_file_location("asset_disk_guard", Path(__file__).parents[2] / "asset_storage.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

@pytest.mark.parametrize("target,uuid,options,error", [
    ("/", "expected", "rw", "not mounted"),
    ("mount", "wrong-disk", "rw", "not mounted"),
    ("mount", "expected", "ro", "read-only"),
])
def test_missing_wrong_or_readonly_mount_rejects_before_directory_creation(tmp_path, monkeypatch, target, uuid, options, error):
    mount = tmp_path / "disk"
    dest = mount / "jiaan/data/new"
    monkeypatch.setenv("COBOT_ASSET_MOUNT", str(mount))
    monkeypatch.setenv("COBOT_ASSET_UUID", "expected")
    payload = {"filesystems": [{"target": str(mount) if target == "mount" else target, "uuid": uuid, "options": options}]}
    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout=json.dumps(payload)))
    with pytest.raises(OSError, match=error):
        guard.require_storage(dest, write=True)
    assert not mount.exists()

def test_expected_disk_accepts_and_development_paths_do_not_probe(tmp_path, monkeypatch):
    mount = tmp_path / "disk"
    monkeypatch.setenv("COBOT_ASSET_MOUNT", str(mount))
    monkeypatch.setenv("COBOT_ASSET_UUID", "expected")
    payload = {"filesystems": [{"target": str(mount), "uuid": "expected", "options": "rw,nosuid"}]}
    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout=json.dumps(payload)))
    assert guard.require_storage(mount / "jiaan/model/a", write=True)["uuid"] == "expected"
    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **kw: pytest.fail("unrelated dev path must not require production disk"))
    guard.require_storage(tmp_path / "fixtures")
