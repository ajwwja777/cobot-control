#!/usr/bin/env bash
# Hardware runtime is owned by cobot-control; no web imports are required.
COBOT_CONTROL_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export COBOT_CONTROL_PROJECT_ROOT
export COBOT_RUNTIME_ROOT="$COBOT_CONTROL_PROJECT_ROOT/runtime"
# JSON is data; export only allowlisted keys with shell quoting.
_cobot_exports="$(PYTHONPATH="$COBOT_CONTROL_PROJECT_ROOT/src" /usr/bin/python3 -m cobot_control.shell_environment)" || return 1
eval "$_cobot_exports"
unset _cobot_exports
export PYTHONPATH="$COBOT_CONTROL_PROJECT_ROOT/scripts/ros_log_compat${PYTHONPATH:+:$PYTHONPATH}"
export ROS_HOME="$COBOT_RUNTIME_ROOT/ros"
export ROS_LOG_DIR="$ROS_HOME/logs"
mkdir -p "$ROS_LOG_DIR"
