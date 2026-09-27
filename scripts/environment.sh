#!/usr/bin/env bash
# Hardware runtime is owned by cobot-control; no web imports are required.
COBOT_CONTROL_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export COBOT_CONTROL_PROJECT_ROOT
export COBOT_RUNTIME_ROOT="$COBOT_CONTROL_PROJECT_ROOT/runtime"
export TASK5_ROS_SETUP="${TASK5_ROS_SETUP:-/home/agilex/cobot_magic/Piper_ros_private-ros-noetic/devel/setup.bash}"
export PYTHONPATH="$COBOT_CONTROL_PROJECT_ROOT/scripts/ros_log_compat${PYTHONPATH:+:$PYTHONPATH}"
export ROS_HOME="$COBOT_RUNTIME_ROOT/ros"
export ROS_LOG_DIR="$ROS_HOME/logs"
mkdir -p "$ROS_LOG_DIR"
