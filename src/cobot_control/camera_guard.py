"""Read-only detection of foreign camera USB owners before a second launch."""
import os
from pathlib import Path


def usb_camera_conflicts(managed_pids=(), *, proc=Path("/proc")):
    managed={int(pid) for pid in managed_pids}
    groups=set()
    for pid in managed:
        try:groups.add(os.getpgid(pid))
        except OSError:pass
    conflicts=[]
    for directory in proc.glob("[0-9]*"):
        try:
            raw=(directory/"stat").read_text();fields=raw[raw.rfind(")")+2:].split()
            if fields[0]=="Z":continue
            argv=(directory/"cmdline").read_bytes().decode(errors="replace").split("\0")
            if not argv or Path(argv[0]).name!="astra_camera_node":continue
            command=" ".join(argv)
            if not any("/camera_"+side+"/" in command for side in ("f","l","r")):continue
            if int(directory.name) in managed or int(fields[2]) in groups:continue
            # Managed launches may put a driver in a separate process group.
            parent=int(fields[1]);seen=set()
            while parent>1 and parent not in seen and parent not in managed:
                seen.add(parent);text=(proc/str(parent)/"stat").read_text();parent=int(text[text.rfind(")")+2:].split()[1])
            if parent in managed:continue
            devices=[]
            for fd in (directory/"fd").iterdir():
                try:
                    target=os.readlink(fd)
                    if target.startswith("/dev/bus/usb/"):devices.append(target)
                except OSError:pass
            if devices:conflicts.append({"pid":int(directory.name),"devices":sorted(set(devices)),"command":command})
        except (OSError,ValueError,IndexError):continue
    return conflicts
