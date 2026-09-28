"""Validate the registered external asset disk before reading or writing assets."""
import json
import os
from pathlib import Path
import subprocess

DEFAULT_MOUNT = "/media/agilex/Getea1"
DEFAULT_UUID = "3A0A7A0E0A79C801"

def require_storage(path, write=False):
    target = Path(path).expanduser().absolute()
    mount = Path(os.environ.get("COBOT_ASSET_MOUNT") or DEFAULT_MOUNT)
    if target != mount and mount not in target.parents:
        return  # Development/test paths are not production assets.
    if mount != target.resolve() and mount not in target.resolve().parents:
        raise OSError("Asset path escapes the registered disk: " + str(target))
    try:
        result = subprocess.run(
            ["findmnt", "-J", "-T", str(mount), "-o", "TARGET,UUID,OPTIONS"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise OSError("Cannot verify Getea1 mount: " + str(error)) from error
    try:
        info = json.loads(result.stdout)["filesystems"][0]
    except (ValueError, KeyError, IndexError):
        info = {}
    expected = os.environ.get("COBOT_ASSET_UUID") or DEFAULT_UUID
    if result.returncode or info.get("target") != str(mount) or info.get("uuid") != expected:
        raise OSError("Getea1 is not mounted correctly; check the disk and mount before retrying. No storage directory was created.")
    if write and "rw" not in info.get("options", "").split(","):
        raise OSError("Getea1 is read-only; restore writable storage before retrying.")
    return info

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(require_storage(args.path, args.write), ensure_ascii=False))
