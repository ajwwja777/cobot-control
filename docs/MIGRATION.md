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

## 2026-09-29：职责边界与部署材料

按实际源码、只读现场状态整理，代码先在A6000开发。结构、安装、依赖来源及验证界限见docs/DEPLOYMENT.md；跨项目关系见cobot-web/docs/ARCHITECTURE.md。数据/模型实体未迁移或删除；公共厂商工作区未删除、硬件未重启。guide只写事实、不提交其Git。现场切换与版本见后续发布回执。

## 2026-09-29：正式切换、清理及交付验收

硬件规则与独立管理入口已提交 c933bcb 并同步现场。web 关闭期间，control.py status 仍能识别相机 PID 524014；web 恢复后 PID 与状态一致。重复启动、PID复用、进程组停止和不误伤无关任务由3个真实无害进程测试覆盖；本批没有以真机启停代替离线测试。

Piper/Astra/SDK 精确源码快照、系统配置来源、包版本、机器模板和安装脚本已登记。A6000空目录恢复源码通过；干净catkin构建受Docker代理故障阻挡，仍待验证。公共工作区未删除，aloha未升级。后续自定义camera launch的停止匹配也读取同一机器配置。

主代码位于 /data/LFT-W02_data/jiaan/jiaan/projects/cobot-control；现场副本 /home/agilex/jiaan/project/cobot-control。后续收尾版本以Git main和现场.release.json为准。guide仅更新事实摘要，不提交其Git。

## 2026-09-29 12:02：五臂 CAN 无接收后恢复的只读排查

来源：用户提供 can_up.sh 输出，五臂均 ERROR-ACTIVE 且收不到数据；USB 重插未恢复，重新插接同时承载电源和 CAN 的臂端线后恢复。未确认是单一公共连接还是分别操作各臂，不能据此判定某一个接点故障。

核对实际源码：can_up.sh 转发 can_config_cobot.sh task2；“已就绪”只判断名称/UP/bitrate/restart-ms，接收检查是 0.5 秒 rx_packets 是否增长。ERROR-ACTIVE 本身不是故障结论，也不能证明机械臂已在发送反馈。五臂 1 Mbit/s；can0 500 kbit/s 是另一路既有配置。本轮没有执行 can_up、接口复位、控制帧或机械臂运动。

现场 12:02 后只读两秒采样：五路各新增约 6,090 接收帧，rx_errors/tx_errors 增量为零，当前 CAN 接收已恢复。内核 11:55:35–36 有 50 条 gs_usb “Unexpected unused echo id”记录；11:57:37–46 记录五适配器依次断开/重枚举，11:57:55–56 恢复命名。echo 告警不能单独证明根因，拔插后的零错误统计也不能还原拔插前计数。

推断：恢复动作同时改变了供电/控制器启动状态与 CAN 接触，优先考虑臂端供电、初始化或连接问题；尚不能区分接触不良与上电后控制器未正常工作，也不能完全排除适配器/共享链路。未修改代码、环境、驱动或运行服务。

证据：A6000 /data/LFT-W02_data/jiaan/jiaan/projects/cobot-control/outputs/diagnostics/can-reconnect-20260929/；Cobot /home/agilex/jiaan/project/cobot-control/runtime/diagnostics/can-reconnect-20260929/。包含 can-counters.json 与 kernel.log。

## 2026-09-29：中臂首次归位与示教健康修正

来源：用户首次上电 home 被 mode=0 拒绝、需先 recover；后臂示教无法同步且面板状态错误。核对原驱动后确认：自动使能不等于进入 CAN 控制，原驱动在收到第一条 JointState 时才调用 MotionCtrl_2(1,1,100)，旧 home 却在此前强制要求 mode=1。robot/mid_home.py 现允许无故障 standby 进入准备阶段；被动读取 can_mid 确认六关节已使能、无保护/示教/其他控制帧后，向已有 ROS 驱动发送实测原位姿一次，保留夹爪开度。两秒内确认 ROS/CAN 均 mode=1 且六关节已使能，才执行原限速归位。未嵌入完整 Recover，未增加自动清错/失能/使能，已有模式1路径不重复初始化。控制权、Session 暂停检查和 home/recover 共用锁保留。

显示解析错误：真实后臂示教为 mode=2、teach=1；teach=2 是退出残留。修正 control 的 CAN 分类；只有实际按钮、协调器接管、新鲜指令与前臂跟踪均成立且双方健康才蓝色，夹爪继承前臂（自身故障除外）。增加逐环节 sync_issue、过期话题、最大关节误差、配对故障；前臂不再错误显示后臂的 CAN 原始状态。控制语义、话题、夹持偏移和发送频率未改。

真实不同步另有发送链路故障：左右 can_left/right 接收持续增长，但发送计数连续采样停在 40874/61331，队列各积压10帧，累计 qdisc drops 为53002/35739。托管 arms 日志有88741条发送失败；协调器已经识别按钮并进入 manual/following。12:06:58–12:07:47 内核 gs_usb 多次报告 Unexpected unused echo id，与本次发送堵塞时间重合；现场内核5.15.0-102。只能确定发送通路异常，尚不能断言适配器固件/USB连接/驱动哪一项是最终根因。[Linux 5.15驱动源码](https://github.com/torvalds/linux/blob/v5.15/drivers/net/can/usb/gs_usb.c)可用于理解 echo 上下文，不代表已核验现场 Ubuntu 全部补丁。

新增 src/cobot_control/can_health.py 只读 tc/sysfs：非空队列至少1秒无 TX 进展才报堵塞，历史丢帧数字本身不触发当前故障。网页与独立CLI共用该判定；不自动复位、发送试探帧或改变控制频率。完整恢复前须停止推理/示教并支撑机械臂，沿既有 scoped Recover 执行；本批不擅自操作现场硬件。

证据：A6000 outputs/diagnostics/teach-and-mid-20260929/；现场 runtime/diagnostics/teach-and-mid-20260929/。首轮384项离线回归、收尾190项硬件/网页设备回归通过。中臂冷上电首次归位、堵塞后的受控恢复和真实示教跟踪尚待现场验收；不能把离线通过等同动作已验证。发布及同步结果另记。

### 发布与已授权的现场恢复

control 20aff53 / fba6fe5、web c863f60 / 55c572f 已 push 核对远端，同步 Cobot 146 / 197 文件并逐项SHA校验。只重载网页，原臂launch PID1318293及相机进程保留；中臂 CLI 每次调用读取新实现，无需重启驱动。

用户随后明确确认已停止推理、松开示教、前臂已支撑且周围无人，授权恢复前双臂及小距离验证。通过 control.py recover front-pair --execute 调用既有受控恢复，单独复位 can_left/right，队列10→0、六关节使能且无故障，协调器复位完成。未启动模型。独立CLI退出后该托管任务因无父进程收取退出码被标记stale；不将这个状态伪造为completed，真实结果由恢复日志和后续反馈/动作验证交叉确认。

12:39 使用原 home_front 服务，让前双臂第一关节各+0.01 rad，保留其他关节和夹爪，再返回实测原位；没有另起控制发布者。实测位移左0.01020474、右0.00943720 rad；返回最大误差左0.00045354、右0.00020933 rad，验证通过。临时ROS归位参数完整恢复，未改正式位姿文件；脚本与数值证据在 small_motion_check.py / small-motion.json。

第一次现场示教黄灯复测发现新增健康逻辑把latched的handover_mode/fault误当周期心跳；已在fba6fe5纠正，55c572f补回归并重载网页。24项健康回归通过。后臂反馈、按钮、前臂与指令仍要求实时；模式/故障沿真实“变化时发布”协议判断，不因状态保持而超时。该次示教期间CAN队列为空，drops没有新增，黄灯不能误报为CAN再次堵塞。真实示教颜色/跟踪的第二次复测、中臂冷上电首次home仍分别待记录。
