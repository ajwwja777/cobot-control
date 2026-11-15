"""Deletion of one explicitly selected trace under the recorder/replay lock."""
import fcntl
from pathlib import Path
import re


def delete_trace(root, name, *, lock_file):
    root=Path(root).absolute()
    if root.resolve()!=root or not re.fullmatch(r"teleop-[A-Za-z0-9_-]+[.]jsonl",name):
        raise ValueError("invalid_trace")
    lock_file=Path(lock_file);lock_file.parent.mkdir(parents=True,exist_ok=True)
    with lock_file.open("a+") as guard:
        try:fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError("已有录制或回放，暂不能删除轨迹")
        path=root/name;metadata=path.with_suffix(".name.json");pointer=root/"latest.txt"
        for candidate in [path,metadata,pointer]:
            if candidate.is_symlink() or (candidate.exists() and not candidate.is_file()):raise ValueError("invalid_trace_entry")
        if not path.is_file():raise ValueError("trace_not_found")
        clear_latest=pointer.is_file() and pointer.stat().st_size<=4096 and pointer.read_text().strip()==name
        path.unlink()
        if metadata.exists():metadata.unlink()
        # Do not silently replace the user's deleted default with another motion.
        if clear_latest:pointer.unlink()
        return {"deleted":name,"latest_cleared":clear_latest}
