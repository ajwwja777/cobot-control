"""Hardware tests cannot contact a ROS master on a development machine."""
import importlib.util
import sys
from types import ModuleType

if importlib.util.find_spec("rosgraph") is None:
    module = ModuleType("rosgraph")
    def unmocked_master(*args, **kwargs):
        raise AssertionError("Test must provide its fake ROS master")
    module.Master = unmocked_master
    sys.modules["rosgraph"] = module
