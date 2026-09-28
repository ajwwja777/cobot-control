#!/usr/bin/env bash
# Rebuild only the required ROS packages, not the vendor's complete workspace.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/third_party/site-hardware"
WORKSPACE="$ROOT/runtime/build/hardware_ws"
if [[ "${1:-}" != --build ]]; then
  echo "Restore scripts/restore_hardware.py archive into $SOURCE"
  echo "Then ./scripts/build_hardware.sh --build (ROS Noetic and rosdep dependencies must already be installed)"
  exit 0
fi
[[ -f /opt/ros/noetic/setup.bash ]] || { echo "Install ROS Noetic first"; exit 2; }
mkdir -p "$WORKSPACE/src"
for package in piper_msgs piper_description; do
  [[ -d "$SOURCE/piper_ros_src/$package" ]] || exit 2
  [[ -e "$WORKSPACE/src/$package" ]] || ln -s "$SOURCE/piper_ros_src/$package" "$WORKSPACE/src/$package"
done
[[ -e "$WORKSPACE/src/astra_camera" ]] || ln -s "$SOURCE/astra_camera" "$WORKSPACE/src/astra_camera"
# A clean environment prevents capturing Desktop/agilex_ws or another user's overlay.
env -i HOME="$HOME" PATH=/usr/local/bin:/usr/bin:/bin LANG=C.UTF-8 bash -c '
  set -e
  source /opt/ros/noetic/setup.bash
  cd "$1"
  catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
' build "$WORKSPACE"
echo "Set ros_setup in configs/local.json to $WORKSPACE/devel/setup.bash after checking the build."
