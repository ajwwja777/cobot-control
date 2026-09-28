"""Hardware launch selection shared by terminal and browser; saving never starts hardware."""
import json
import os
import shlex
import threading
from pathlib import Path
from uuid import uuid4
from .paths import PROJECT, RUNTIME_ROOT, SETTINGS
STATE = RUNTIME_ROOT / "hardware-options.json"
LOCK = threading.RLock()

def read():
    try:
        value = json.loads(STATE.read_text())
        if not isinstance(value, dict):
            raise ValueError("Invalid site options")
        return value
    except FileNotFoundError:
        return {}


def write(value):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_name(STATE.name + "." + uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    os.replace(temporary, STATE)


def roots():
    values = [PROJECT.parent, Path.home()]
    setup = SETTINGS.get("ros_setup")
    if setup:
        values.append(Path(setup).parent.parent)
    values.extend(Path(p) for p in SETTINGS.get("extension_roots", []))
    return list(dict.fromkeys(p.expanduser().resolve() for p in values))


def checked_path(value, *, directory=None):
    path = Path(value).expanduser()
    if not value or not path.is_absolute():
        raise ValueError("Please choose an absolute server path / 请选择服务器绝对路径")
    path = path.resolve(strict=True)
    if not any(path == root or root in path.parents for root in roots()):
        raise ValueError("Path outside configured roots; add extension_roots in configs/local.json / 路径超出允许范围")
    if directory is True and not path.is_dir():
        raise ValueError("Directory required / 请选择目录")
    if directory is False and not path.is_file():
        raise ValueError("File required / 请选择文件")
    return path


def hardware():
    return read().get("hardware", {})


def device_marker(component, fallback):
    entry = hardware().get(component)
    return entry["path"] if entry else fallback


def hardware_terminal(entry):
    path = Path(entry["path"])
    relative = "./" + path.name if str(path.parent) == entry["cwd"] else str(path)
    lines = ["cd " + shlex.quote(entry["cwd"])]
    if entry.get("setup"):
        lines.append("source " + shlex.quote(entry["setup"]))
    lines.append(("roslaunch " if path.suffix == ".launch" else "bash ") +
                 " ".join(shlex.quote(x) for x in [relative, *entry.get("args", [])]))
    return "\n".join(lines)


def device_command(component):
    entry = hardware().get(component)
    if not entry:
        return None
    path = checked_path(entry["path"], directory=False)
    setup = entry.get("setup", "")
    if setup:
        setup = str(checked_path(setup, directory=False))
    return ["/usr/bin/python3", str(PROJECT / "scripts/site_device.py"),
            "--component", component, "--path", str(path), "--setup", setup,
            "--cwd", str(checked_path(entry["cwd"], directory=True)), "--", *entry.get("args", [])]


def save_hardware(component, path, setup="", cwd="", args=None):
    if component not in {"arms", "cameras"}:
        raise ValueError("Unsupported hardware component")
    with LOCK:
        state = read()
        config = state.setdefault("hardware", {})
        if not path:
            config.pop(component, None)
        else:
            target = checked_path(path, directory=False)
            if target.suffix not in {".sh", ".launch"}:
                raise ValueError("Choose a .sh or ROS 1 .launch file")
            if target.suffix == ".launch" and not setup:
                raise ValueError("ROS .launch requires its environment setup.bash")
            if setup:
                checked_path(setup, directory=False)
            directory = checked_path(cwd or str(target.parent), directory=True)
            config[component] = {"path": str(target), "setup": setup, "cwd": str(directory), "args": args or []}
        write(state)
