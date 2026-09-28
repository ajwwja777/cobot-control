#!/usr/bin/env python3
"""Restore the recorded hardware source into an empty directory; never start devices."""
import argparse
import hashlib
from pathlib import Path
import tarfile
import shutil
SHA256="e7165305efba36595d6c5058776469c4080a5eace38a300ff05ab993297312d9"
def restore(archive, destination):
    digest=hashlib.sha256()
    with archive.open("rb") as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b""):digest.update(block)
    if digest.hexdigest()!=SHA256:raise ValueError("Hardware archive SHA256 mismatch")
    destination=destination.resolve()
    if destination.exists() and any(destination.iterdir()):raise ValueError("Destination must be empty")
    destination.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive) as source:
        members=source.getmembers()
        for item in members:
            target=destination/item.name
            if target.resolve()!=destination and destination not in target.resolve().parents:
                raise ValueError("Unsafe archive member "+item.name)
            if item.issym() or item.islnk():
                # Generated catkin CMake link is rebuilt by catkin_init_workspace.
                if item.name=="piper_ros_src/CMakeLists.txt":continue
                link=Path(item.linkname)
                resolved=(target.parent/link).resolve()
                if link.is_absolute() or destination not in resolved.parents:
                    raise ValueError("External archive link "+item.name)
            elif not item.isfile() and not item.isdir():
                raise ValueError("Unsupported archive member "+item.name)
        for item in members:
            if item.name=="piper_ros_src/CMakeLists.txt" and item.issym():continue
            source.extract(item,destination)
    print(destination)
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive",type=Path)
    parser.add_argument("destination",type=Path)
    args=parser.parse_args();restore(args.archive,args.destination)
