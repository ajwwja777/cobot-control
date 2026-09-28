# 硬件源码来源

前臂／中臂节点从现场实际运行文件原样复制：/home/agilex/cobot_magic/Piper_ros_private-ros-noetic/src/piper/scripts/piper_start_ms_node.py

SHA256: 64a3a55424eec91117c5ff48f5714c1a80886e432357dd5b1b43ab5c09de5968

后臂、示教交接、归位、恢复和 CAN 工具来自 cobot-web d5fe477；模块及 ROS topic/service 名称保留。启动入口与运行日志归 cobot-control。系统 ROS / catkin 消息和 Piper SDK 是已安装的依赖，尚不属于本项目业务源码。

## 系统 CAN recovery helper

2026-09-28 将现场 /usr/local/sbin/cobot-can-recover-one 原始源码保存到 scripts/system/cobot-can-recover-one，bash -n通过；SHA-256 630a3b8ce7f9da3253c52047946e2e3c4e6eaabbadbe2397cd7187d8dc400a20。现有安装与sudo策略未改动。

新机器由管理员核对脚本后安装为root所有、0755，沿用仅允许该helper处理已登记CAN的sudo白名单。不要对普通用户可写的项目脚本直接配置免密root执行。项目can_recover_one.sh调用该系统入口。


## 2026-09-28 现场依赖快照

configs/environments/cobot-hardware.json 记录实际OS、Python、ROS Debian包版本与SDK位置。现场Ubuntu20.04，系统Python3.8.10；aloha Python3.8.19、piper-sdk0.4.1、python-can4.4.2、numpy1.23.4。现有Piper ROS工作区无可用Git登记，不能只靠包名推定精确源码。

A6000与Cobot本项目outputs/environments/hardware-source-20260928.tar.gz保存Piper ROS src、astra_camera和已安装piper_sdk的源码快照：1,374文件/链接逐项SHA及链接文本验证通过，压缩包70,960,259字节，SHA-256 e7165305efba36595d6c5058776469c4080a5eace38a300ff05ab993297312d9。配套JSON保留源路径、每文件哈希、排除的Git/cache条目和A6000校验状态。原已安装依赖未移动、未删除。

这是源码恢复依据，不是完整系统镜像或已验证的一键重装。恢复另一台机器时仍需ROS系统依赖、catkin构建、USB/udev与CAN配置，并进行硬件验收；不能把压缩包存在当作驱动已安装。本次没有升级任何SDK或ROS包。
