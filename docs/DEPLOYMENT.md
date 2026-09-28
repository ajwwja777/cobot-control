# 部署与独立硬件管理

## 材料与位置

- A6000 主代码：/data/LFT-W02_data/jiaan/jiaan/projects/cobot-control。
- Git：https://github.com/ajwwja777/cobot-control。
- Cobot 副本：/home/agilex/jiaan/project/cobot-control。
- 现场数据：/media/agilex/Getea1/jiaan/data；位姿 motion/poses/home_poses.yaml。
- 本项目日志、PID 与任务身份：runtime/devices；旧任务日志可继续引用其原路径。
- 依赖来源与源码快照：[HARDWARE_SOURCE.md](HARDWARE_SOURCE.md)。

## 安装与机器配置

~~~bash
cd /home/agilex/jiaan/project
git clone https://github.com/ajwwja777/cobot-control.git
cd cobot-control
python3 -m venv .venv
.venv/bin/python -m pip install .
cp configs/machine.example.json configs/local.json
~~~

在 configs/local.json 填写 ROS setup、硬件 Python、Conda setup、ROS master、
CAN 映射、相机 launch 和位姿路径；COBOT_CONTROL_CONFIG 可选择另一份配置。
已有环境变量优先。.venv 是管理工具环境；hardware_python 指向驱动已有的 aloha 环境。
当前驱动为 Python 3.8.19、piper-sdk 0.4.1、python-can 4.4.2、numpy 1.23.4。
不要在安装管理工具时升级驱动 SDK。版本记录不等同于完整可重建环境锁文件；
后续依赖审计与重建结果见迁移记录。

## 网页与终端的共用管理入口

~~~bash
cd /home/agilex/jiaan/project/cobot-control
.venv/bin/python scripts/control.py status
.venv/bin/python scripts/control.py start roscore
.venv/bin/python scripts/control.py start arms
.venv/bin/python scripts/control.py start cameras
~~~

启动机械臂沿用既有使能语义，应在现场满足安全条件时执行。
管理入口为每个任务建立独立进程组，stdout/stderr 写日志，保存 PID 和 start_ticks。
它不打开可视终端；后台进程相当于多个终端各运行一个前台 launch。
关闭网页后，硬件仍可通过本入口管理。

~~~bash
cd /home/agilex/jiaan/project/cobot-control
.venv/bin/python scripts/control.py stop cameras
.venv/bin/python scripts/control.py stop arms
.venv/bin/python scripts/control.py stop roscore
~~~

停止向核验后的进程组发送 SIGINT（Ctrl+C）；先停相机和臂，再停 ROS。
同名但位于其他目录的 launch 不属于本项目。修改启动路径前先停止对应硬件任务。

~~~bash
cd /home/agilex/jiaan/project/cobot-control
.venv/bin/python scripts/control.py configure-launch cameras --path /absolute/camera.launch --setup /absolute/devel/setup.bash
.venv/bin/python scripts/control.py can configure
~~~

CAN 密码交互读取，不写日志。直接终端入口是 scripts/can_up.sh，实际调用
integrations/legacy_control/can_config_cobot.sh task2；网页 can_web.sh 调同一配置实现。
CAN reset 保留原 1 Mbps / restart-ms 100。

## 被动诊断和归位

~~~bash
cd /home/agilex/jiaan/project/cobot-control
source scripts/environment.sh
source "$TASK5_ROS_SETUP"
"$COBOT_HARDWARE_PYTHON" scripts/control.py diagnose --seconds 2
.venv/bin/python scripts/control.py home selection --arms mid,front-right --pose plug2
~~~

diagnose 只订阅反馈、读 CAN 与 ROS graph，不发布动作。最后一条只显示计划；
现场确认后加 --execute 执行。真实调用仍是 scripts/home.sh selected --targets
mid,front-right --pose plug2 --yes，进入 robot/home.py。
原 home.sh、recover.sh 等前台入口保留，可直接用终端 Ctrl+C 停止。

## 接口与验证边界

同款设备更换机器配置；不同硬件需实现 ros_topics.py 的反馈、控制权与单位协议，
以及 robot 层适配，并单独验收。不能仅改目录便宣称动作兼容。

2026-09-29：67 项网页兼容测试和 3 项独立进程管理测试通过。
包括终端接管、重复启动阻止、PID 复用拒绝、停止不影响另一进程。未执行硬件运动。
新机器驱动重建、上电示教、归位和真实推理仍需分别验收。

## 2026-09-29：换机材料与机器配置

除Git外，取A6000本项目outputs/environments/hardware-source-20260928.tar.gz；SHA256已写入scripts/restore_hardware.py。恢复脚本只写空目录，拒绝越界链接，旧生成的catkin CMake链接由新构建替代。Piper/Astra现场源码无Git信息，按哈希快照保留，不能假称某个原厂revision。

```bash
cd /home/agilex/jiaan/project/cobot-control
./scripts/install.sh
python3 scripts/restore_hardware.py outputs/environments/hardware-source-20260928.tar.gz third_party/site-hardware
./scripts/install_hardware_python.sh
source /opt/ros/noetic/setup.bash
rosdep install --from-paths third_party/site-hardware/piper_ros_src/piper_msgs third_party/site-hardware/piper_ros_src/piper_description third_party/site-hardware/astra_camera --ignore-src -r -y
./scripts/build_hardware.sh --build
```

前提为Ubuntu20.04、ROS Noetic及rosdep已安装；系统精确包版本见configs/environments/system-packages.tsv。build_hardware只构建piper_msgs/piper_description/Astra，不编译整棵导航/Interbotix。configs/local.json填新runtime/build/hardware_ws/devel/setup.bash，hardware_python填envs/hardware/bin/python，conda_setup留空使用venv。现场aloha不升级、不切换；本批提供的是新机器安装入口。

can_usb_ports与camera_serials在configs/machine.example.json外置。稳定can_left/right/mid/rear_left/rear_right是现有协议的一部分；换USB口只换端口映射，不能只改健康显示名称。控制参数、ROS topic/service和示教安全语义未改。

系统helper/udev/sudoers保留原安装位置，scripts/system保存源码与例子。管理员审核后可运行scripts/install_system.sh的显式--apply模式；该入口不触发USB重枚举、不配置CAN、不启动机械臂。arx_can.rules仅留历史证据，不盲目安装。来源/哈希见configs/environments/site-dependencies.json。

camera_ws生成配置引用/home/agilex/agilex_ws/devel，但该目录已不存在；新构建不带入它。Desktop/agilex_ws是底盘/导航组件，标准五臂入口不需要。历史adapter仍有source，未删除公共目录；换机使用项目入口，不照搬他人桌面工作区。

已验证源码SHA、空目录恢复、control Python隔离安装、只读状态与进程测试。A6000 Docker Noetic拉取被失效127.0.0.1:7890代理阻断；catkin干净构建、USB/驱动与真实示教仍待验证，不能声称完整硬件重装通过。
