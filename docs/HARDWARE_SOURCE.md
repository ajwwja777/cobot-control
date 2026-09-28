# 硬件源码来源

前臂／中臂节点从现场实际运行文件原样复制：/home/agilex/cobot_magic/Piper_ros_private-ros-noetic/src/piper/scripts/piper_start_ms_node.py

SHA256: 64a3a55424eec91117c5ff48f5714c1a80886e432357dd5b1b43ab5c09de5968

后臂、示教交接、归位、恢复和 CAN 工具来自 cobot-web d5fe477；模块及 ROS topic/service 名称保留。启动入口与运行日志归 cobot-control。系统 ROS / catkin 消息和 Piper SDK 是已安装的依赖，尚不属于本项目业务源码。

## 系统 CAN recovery helper

2026-09-28 将现场 /usr/local/sbin/cobot-can-recover-one 原始源码保存到 scripts/system/cobot-can-recover-one，bash -n通过；SHA-256 630a3b8ce7f9da3253c52047946e2e3c4e6eaabbadbe2397cd7187d8dc400a20。现有安装与sudo策略未改动。

新机器由管理员核对脚本后安装为root所有、0755，沿用仅允许该helper处理已登记CAN的sudo白名单。不要对普通用户可写的项目脚本直接配置免密root执行。项目can_recover_one.sh调用该系统入口。
