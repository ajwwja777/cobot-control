"""Print only allowlisted hardware settings with POSIX shell quoting."""
import os
import shlex
from .paths import PROJECT, SETTINGS
DEFAULTS = {
    "TASK5_ROS_SETUP": ("ros_setup", "/home/agilex/cobot_magic/Piper_ros_private-ros-noetic/devel/setup.bash"),
    "COBOT_HARDWARE_PYTHON": ("hardware_python", "/home/agilex/miniconda3/envs/aloha/bin/python"),
    "COBOT_CONDA_SETUP": ("conda_setup", "/home/agilex/miniconda3/etc/profile.d/conda.sh"),
    "ROS_MASTER_URI": ("ros_master_uri", "http://localhost:11311"),
    "COBOT_CAMERA_LAUNCH": ("camera_launch", str(PROJECT / "integrations/legacy_control/launch/multi_camera_shuai.launch")),
}
for variable, (key, default) in DEFAULTS.items():
    value = os.environ.get(variable, SETTINGS.get(key, default))
    if key == "camera_launch" and not os.path.isabs(value):
        value = str(PROJECT / value)
    print("export " + variable + "=" + shlex.quote(str(value)))
