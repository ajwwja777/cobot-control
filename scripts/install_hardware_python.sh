#!/usr/bin/env bash
# New machine only; SDK source is the exact audited snapshot, never an unpinned upgrade.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -d "$ROOT/third_party/site-hardware/piper_sdk" ]] || { echo "Restore hardware source first"; exit 2; }
uv venv --python 3.8 "$ROOT/envs/hardware"
uv pip install --python "$ROOT/envs/hardware/bin/python" numpy==1.23.4 python-can==4.4.2 PyYAML==6.0.3 rospkg==1.6.1 catkin-pkg==1.1.0
"$ROOT/envs/hardware/bin/python" - "$ROOT" <<'PYSDK'
import sys,sysconfig
from pathlib import Path
root=Path(sys.argv[1])
(Path(sysconfig.get_paths()["purelib"])/"cobot-site-sdk.pth").write_text(str(root/"third_party/site-hardware")+"\n")
import site
site.addsitedir(sysconfig.get_paths()["purelib"])
import piper_sdk,can,numpy
print(piper_sdk.__file__,can.__version__,numpy.__version__)
PYSDK
echo "Set hardware_python to $ROOT/envs/hardware/bin/python and conda_setup to an empty string."
