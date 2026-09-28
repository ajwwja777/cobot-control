# Cobot 硬件与独立前后双臂控制：迁移记录

日期：2026-09-27。当前业务迁移进度见文末；以下初始化内容保留为历史记录。

## 已有位置与成果

以下是已读项目记录与前序目录核验的入口清单，不表示本轮重新完整验证每项资产。执行某批迁移前须核对实际目录、符号链接、Git 状态和使用者。

| 机器 | 旧位置／已有依赖 | 保留事项 |
|---|---|---|
| Cobot | `/media/agilex/Getea1/jiaan/projects/cobot-platform/robot/arms` | 现有机械臂控制代码；待按实际调用链逐项核对。 |
| Cobot | `/media/agilex/Getea1/jiaan/projects/cobot-platform/scripts` | 现有启动、归位和恢复入口；与网页、运维共有调用关系，不能整体重复搬迁。 |
| Cobot | `/home/agilex/cobot_magic/Piper_ros_private-ros-noetic` | 现用 ROS 源码与依赖；先核验来源、共享使用者和构建路径，不删除他人或共享原件。 |
| A6000 | `/data/LFT-W02_data/jiaan/projects/proj-20260829-cobot-realworld-vla` | 旧控制与 Task2/HIL 契约记录，保留未提交改动。 |

## 首个候选验收范围

选择一个可隔离的设备状态查询入口，核清依赖后复制到新位置，比较新旧状态语义和错误处理；第一批不改变运动逻辑。

验收要求：新入口可独立执行，只读查询不触发运动；正确报告设备未启动／异常；不再依赖计划清理的旧代码路径。涉及运动的后续批次必须另做现场验收。

## 逐批迁移约定

一次只处理一个明确范围，记录来源、目标、依赖、版本／校验值和回退入口；先复制与验证，再切换，最后清理对应旧文件。未验收不切换，仍被依赖或缺少可靠备份的原件不清理。共有目录按文件实际归属处理，保留其他对话的未提交修改及共享资产。

迁移批次记录至少包括：范围、来源与目标、验证结果、切换状态、可清理清单及实际清理结果。初始化完成仅表示入口与 Git 可接管，不代表运行环境或业务功能已验收。

本轮没有迁移／删除旧文件，没有安装项目运行环境、启动训练、加载模型或控制机器人，也没有变更当前网页服务。

## 初始化发布记录

- 2026-09-27：项目目录与维护入口已建立，基础提交已 push 并核对远端 main 一致。
- 仓库：https://github.com/ajwwja777/cobot-control（独立仓库，非 GitHub fork）。
- 首次发布提交：`ff565f2abe977473c7e2f087cfa48b13d4a841bd`。
- 本记录在首次发布验证后追加并单独提交；最新版本以 main 为准。
- 运行状态：源码／文档基础已发布，业务迁移、环境安装及新位置运行验收尚未开展。

## 2026-09-27 硬件提取（进行中）

从 cobot-web d5fe477 提取 robot、integrations/legacy_control、硬件 scripts 和位姿配置，保留运动／示教语义。前臂及中臂实际节点从 Piper workspace 复制，SHA 见 HARDWARE_SOURCE.md。A6000 为主代码和 Git；Cobot 目标为 /home/agilex/jiaan/project/cobot-control。旧 launch 进程退出、新位置静态及状态检查通过前不删除旧项目。当前切换尚待验证，未进行真机动作测试。

## 2026-09-27 23:55：源码发布与节点切换前状态

源码 942d459a5d6c45a54a49ff86cedf46f6a3e4c6e6 已 push；Cobot /home/agilex/jiaan/project/cobot-control 同步 111 文件并 SHA-256 核验。硬件测试 342 passed；ROS stub 在未替换调用时明确报错，不会接通真实硬件。新增 CAN recovery 转发仍待下一次同步。位姿来自现场，控制语义未调整。

用户确认机械臂安全断电，可重启节点；本轮仍未执行节点重启或归位。RLT 模型验证期间 Cobot 网络连接中断，需恢复连接后重查进程，再停止旧 launch、从新路径启动和核验。旧项目和网页内硬件兼容副本均未删除。Piper/ROS/Astra 已安装工作区与 aloha SDK 是共享依赖，不属于可整棵删除的旧 cobot-platform。

联动细节与证据：同级 rl-platform/docs/MIGRATION.md 及 outputs/migrations/20260927-rlt/。

## 2026-09-28：新硬件路径被动验收

Cobot已重启，旧平台节点已退出。新项目启动ROS master，显式 front_auto_enable=false、mid_auto_enable=false、rear_auto_enable=false 启动六个臂／交接节点，注册正常。新相机入口三路640×480 RGB8约29.9FPS，5秒126–134帧。两次launch按PID/start_ticks核对后SIGINT正常退出；未归位或发动作。

相机缺少calibration提示在旧现场也存在，没有丢失既有标定。Piper/ROS/Astra/aloha安装工作区作为共享依赖保留，不属于旧cobot-platform整棵清理范围。

网页89个跟踪硬件文件已从A6000 Git移除；Cobot实际部署78个重复文件核对新旧SHA后删除。网页保留轻量入口，位姿唯一来源为本项目configs/home_poses.yaml。

scripts/system/cobot-can-recover-one 保存现场/usr/local/sbin同名root helper原始源码，SHA-256 630a3b8ce7f9da3253c52047946e2e3c4e6eaabbadbe2397cd7187d8dc400a20，bash -n通过；未重新安装或更改root权限。

证据：outputs/migrations/20260928-cutover/cobot/ 的hardware-passive-state.json、hardware-passive-stop.json、camera-readonly.json及launch日志。上电使能、示教与运动仍需现场短轮次验收。

## 2026-09-28：旧平台脱离依赖验证

旧cobot-platform完整归档、检查无活动引用后改名隔离；新正式网页冷启动、经网页任务管理启动三相机并得到三路帧，再正常停止，home.sh --help可用。随后旧平台目录已删除；实际硬件入口、日志、位姿均使用本项目，网页仅转发。删除回执见相邻cobot-web/outputs/migrations/20260928-platform-retirement/cobot/retirement.json。

这次只验证启动路径与相机；没有归位、上电使能或示教动作。现场ROS master保留，臂和相机launch已停止；共享已安装ROS/Piper/Astra/aloha仍保留。

## 2026-09-28：共享依赖保全与最终现场状态

已安装Piper ROS源码、Astra相机源码和piper_sdk源文件快照归本项目outputs/environments/hardware-source-20260928.tar.gz，两机保存，70,960,259字节；1,374文件/链接逐项校验通过，SHA-256 e7165305efba36595d6c5058776469c4080a5eace38a300ff05ab993297312d9。configs/environments/cobot-hardware.json记录系统、ROS和aloha/SDK版本；具体范围见HARDWARE_SOURCE.md。这不是完整操作系统镜像或已经验证的从零环境重建。

本会话的被动验收launch已停止；之后网页新建了arms PID148006（15:25:33）及cameras PID158179（15:34:52），并存在后续归位/恢复任务记录。最终只读检查5/5 CAN、5/5臂节点、3/3相机可用，臂反馈新鲜。保留这些后续任务，不将其误判为旧验收残留。网页与RLT清理没有改变这些硬件进程；本会话未执行归位或真机Episode，HIL/同步动作仍需现场验收。

最终快照由rl-platform/outputs/migrations/20260928-retirement/cobot/final-runtime.json保存。已删除旧cobot-platform和旧RLT；共享ROS/Piper/Astra/aloha依赖继续保留，不能整棵删除cobot_magic。
