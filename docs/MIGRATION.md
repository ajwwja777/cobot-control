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


## 2026-09-28：Getea1 统一存储迁移（进行中）

Cobot 数据与模型统一在 /media/agilex/Getea1/jiaan/data/ 和 /media/agilex/Getea1/jiaan/model/。数据按场景分、模型按项目/模型分；本轮不新增 A6000 权重备份。代码、安装环境、运行日志与 PID 留在 /home/agilex/jiaan/project/<项目>/。完整路径与批次状态见相邻 cobot-web/docs/STORAGE.md。

已在 A6000 接入新存储配置及旧路径映射；逐文件复制/校验正在进行，正式网页已在空闲状态正常停止，机械臂/ROS 进程保留。本段不代表旧源目录已经删除。位姿、回放、示范、RLT rollout/Replay、评测和部署权重按 STORAGE.md 归类。最终运行验证及删除回执待本批完成后追加。

## 2026-09-28 20:00：迁移中遇到 Getea1 USB 掉线

已完成主体 12,059 条目、351,844,176,546 字节及 6 个恢复验证资产、117,047,594 字节的迁移、SHA 校验、运行验收和对应源文件清理。Warmup 与在线模型在新路径加载/释放通过；在线状态 5000/2500/2567，正式权重和 Replay 的 SHA 不变，未启动 Episode 或真机运动。历史读取、92 条有效评测和媒体通过；主副本清理后再次读通。系统盘当时剩余约 404 GiB。

剩余 FluxVLA 环境复制到 libcublasLt.so.12 时出现 I/O error。内核在 19:59:53 将 sda 下线，随后 USB 设备枚举失败；20:00 检查已无 Getea1 块设备和挂载。不能把它归因于单个 Python 包或仅网页错误，也不能仅凭这些日志判定是线缆、供电、硬盘盒或盘本体。

所有迁移进程已退出；正式网页 PID 366090 正常停止，无 GPU 模型进程，临时 ROS master 已停止。本轮未做运动。尚未验收的 FluxVLA 旧目录、暂存副本未清理，**Getea1/jiaan 仅保留 data/model 的目标尚未完成**。已验证结果仅代表掉线前状态，恢复连接后仍须核对文件系统并按迁移收据重新校验新资产，不能直接继续删除或开始在线训练。

证据：相邻 rl-platform/outputs/migrations/20260928-getea-storage/cobot/，现场同目录不带 cobot/。包括 retirement.json、validation/retirement.json、cutover-verification.json、extras/copy-status.json、disk-disconnect.json 和 disk-disconnect-kernel.log。源码和证据位于系统盘/A6000，本轮没有新增 A6000 数据/权重备份。

## 2026-09-28 20:56：Getea1 存储迁移完成

本批已完成复制、哈希与运行验收、切换和对应旧文件清理。Getea1/jiaan 只保留 data、model；旧系统盘数据/模型目录移除。数据按场景/用途/方法归类，位姿与动作回放归 data/motion；模型按项目/模型/场景/版本归类。代码/环境/日志/PID 留在 /home/agilex/jiaan/project/<项目>。

USB 掉线重连后已完成已迁移资产的全量收据复核；尚不能据此认定硬件链路根因已消除。RLT 新路径暂停加载、在线状态恢复与历史媒体通过；FluxVLA 固定版本离线 baseline/prefix-RTC 通过；π0.5 两入口只做 dry-run。本批未启动真实 Episode 或机器人动作。

完整路径、占用、各项验证边界及回执见实际 cobot-web/docs/STORAGE.md。证据位于 rl-platform/outputs/migrations/20260928-getea-storage/cobot/（Cobot 去掉末尾 cobot/）。同批源码与项目记录已按各自仓库发布；guide Git 保持由其他会话管理。

## 2026-09-29：硬件规则共用（第一批，源码验收）

CAN/ROS 探测、健康判定和设备任务管理移到 cobot-control/src/cobot_control；网页保留 HTTP、翻译、RLT/console 扩展和输出展示。新增 control/scripts/control.py，无需网页运行。67 个网页兼容测试、3 个独立进程用例通过。未改变动作/ROS 参数，未执行硬件运动；尚未同步现场。来源：cobot_rlt 本轮跨项目整理。
