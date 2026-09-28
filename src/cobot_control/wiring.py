"""Machine wiring exports; values are validated before becoming shell arguments."""
import argparse
import json
import re
import shlex
from .paths import PROJECT, SETTINGS
def settings():
    return {**json.loads((PROJECT / "configs/machine.example.json").read_text()), **SETTINGS}
def camera_arguments():
    return [key + "_serila_number:=" + value for key, value in settings()["camera_serials"].items()]
def can_shell():
    rows = settings()["can_usb_ports"]
    for port, target in rows.items():
        if not re.fullmatch(r"[0-9.:_-]+", port) or not re.fullmatch(r"can[a-z_0-9]+:(500000|1000000)", target):
            raise ValueError("Invalid CAN USB mapping")
    return "declare -A PORT_MAP=(" + " ".join("[" + shlex.quote(k) + "]=" + shlex.quote(v) for k,v in rows.items()) + ")"
if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("kind", choices=["camera","can"])
    args=parser.parse_args()
    print(can_shell() if args.kind=="can" else "\n".join(camera_arguments()))
