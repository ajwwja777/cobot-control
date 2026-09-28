"""Machine configuration for hardware. Environment overrides configuration."""
import json
import os
from pathlib import Path
PROJECT = Path(__file__).resolve().parents[2]
CONFIG = Path(os.environ.get("COBOT_CONTROL_CONFIG", PROJECT / "configs/local.json"))
SETTINGS = json.loads(CONFIG.read_text()) if CONFIG.is_file() else {}
def path(key, default):
    return Path(os.environ.get("COBOT_" + key.upper(), SETTINGS.get(key, str(default)))).expanduser()
CONTROL = PROJECT
RUNTIME_ROOT = path("control_runtime", PROJECT / "runtime")
DATA = path("data_root", "/media/agilex/Getea1/jiaan/data")
POSE_CONFIG = path("pose_config", DATA / "motion/poses/home_poses.yaml")
