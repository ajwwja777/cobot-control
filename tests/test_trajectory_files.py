import fcntl
from pathlib import Path
import pytest
from cobot_control.trajectory_files import delete_trace


def test_delete_exact_trace_metadata_and_latest_only(tmp_path):
    root=tmp_path/"traces";root.mkdir();selected=root/"teleop-one.jsonl";selected.write_text("one")
    other=root/"teleop-two.jsonl";other.write_text("two");metadata=selected.with_suffix(".name.json");metadata.write_text('{}')
    pointer=root/"latest.txt";pointer.write_text(selected.name+"\n")
    result=delete_trace(root,selected.name,lock_file=tmp_path/"runtime/teleop.lock")
    assert result["deleted"]==selected.name and result["latest_cleared"]
    assert not selected.exists() and not metadata.exists() and not pointer.exists() and other.read_text()=="two"


def test_delete_preserves_unrelated_default_and_refuses_busy_and_symlinks(tmp_path):
    root=tmp_path/"traces";root.mkdir();selected=root/"teleop-one.jsonl";selected.write_text("one")
    pointer=root/"latest.txt";pointer.write_text("teleop-other.jsonl\n");lock=tmp_path/"teleop.lock"
    with lock.open("a+") as guard:
        fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValueError,match="录制或回放"):delete_trace(root,selected.name,lock_file=lock)
    assert selected.read_text()=="one"
    with pytest.raises(ValueError):delete_trace(root,"../teleop-one.jsonl",lock_file=lock)
    selected.with_suffix(".name.json").symlink_to(pointer)
    with pytest.raises(ValueError):delete_trace(root,selected.name,lock_file=lock)
    selected.with_suffix(".name.json").unlink()
    delete_trace(root,selected.name,lock_file=lock)
    assert pointer.read_text()=="teleop-other.jsonl\n"
