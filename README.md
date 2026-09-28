# Cobot 硬件与独立前后双臂控制

## 项目结构

~~~text
cobot-control/
├── src/cobot_control/    # 共用 CAN/ROS 探测、健康判定与任务身份
├── robot/               # 前后臂、示教协调、归位与恢复
├── scripts/             # control.py、硬件启动脚本和系统 helper
├── integrations/        # 已接管的相机 launch 与历史适配
├── configs/             # 机器配置示例、依赖版本
├── tests/               # 无硬件进程管理验收
└── docs/                # 部署、来源与迁移记录
~~~

安装与独立终端入口见 [DEPLOYMENT.md](docs/DEPLOYMENT.md)。网页和终端共用
src/cobot_control，健康规则不再维护在网页中。既有运动脚本保持参数和 ROS 协议。


统一前后双臂独立控制、CAN、ROS、相机、示教按钮、控制权切换、归位与恢复。保留已验证的控制语义和现场操作方式。

## 入口与位置

- 先读统一框架：`/data/LFT-W02_data/jiaan/jiaan/agent-guide/AGENTS.md`。
- A6000 主工作区：`/data/LFT-W02_data/jiaan/jiaan/projects/cobot-control`。
- 笔记本对话入口：`D:\Code\jiaan_workspace\cobot-control`。
- 自有独立仓库：`https://github.com/ajwwja777/cobot-control`（目标分支 `main`）。
- Cobot 运行副本：`/home/agilex/jiaan/project/cobot-control`，按迁移记录分批部署。
- 当前阶段：硬件源码与脚本迁入，现场切换结果见 docs/MIGRATION.md。

## 负责什么

设备发现与状态、硬件启动停止、控制权与示教状态、选择臂和位姿的归位／恢复、底层相机接口。

向采集、VLA、RL 和网页提供设备接口；数据标签与训练 mask 交给 cobot-dagger，模型动作语义交给 vla-platform，网页运行编排与日志交给 cobot-web。物理设备控制权必须统一，调用方不得另起绕过仲裁的控制链路。

## 机器与资产

A6000 负责主代码、Git、维护文档、主要开发验证环境、数据处理和离线评测；训练按资源需要在 A6000／已授权训练机进行。Cobot 只部署本项目现场实际需要的硬件、采集、推理、网页或维护组件，不复制仿真资产和完整训练环境。

Cobot 数据与模型统一在 /media/agilex/Getea1/jiaan/data/ 和 /media/agilex/Getea1/jiaan/model/。数据按场景分、模型按项目/模型分；本轮不新增 A6000 权重备份。代码、安装环境、运行日志与 PID 留在 /home/agilex/jiaan/project/<项目>/。完整路径与批次状态见相邻 cobot-web/docs/STORAGE.md。

## 项目协作

CAN、反馈、相机和归位问题由本项目负责；网页任务／PID 问题交 cobot-web，硬件服务和存储问题在实际负责项目排查；模型输出异常交 vla-platform。

先读本次任务涉及的依赖项目入口和接口说明，再修改相关边界；接口变更要记录受影响调用方与验证方式。常用项目：`cobot-control`、`cobot-dagger`、`vla-platform`、`rl-platform`、`cobot-web`，主工作区均在 `/data/LFT-W02_data/jiaan/jiaan/projects/`。需要专题对话时仍共享所属项目，不因此重复建立业务仓库。

## 下一步

新路径六个臂／交接节点及三相机已在断电条件下验证启动；上电使能、示教、归位与运动待现场短轮次验收。旧cobot-platform已在完整归档和独立运行核验后删除；共享驱动依赖保留。

旧位置、验收条件和切换／清理规则见迁移记录。

来源：2026-09-27 用户确认的项目划分、机器职责与逐批迁移方案；初始化历史保留，当前业务进度见迁移记录。

2026-09-27 归属更新：独立 ops 项目已取消；本次仅修正协作与 runtime 归属，不代表本项目旧业务资产已迁移。

## 硬件入口

scripts/ 下包含 can_up.sh、roscore_up.sh、arms_up.sh、cameras_up.sh、home.sh、recover.sh、front_mode.sh、front_reset.sh 和 teleop.sh。robot/ 是硬件实现，/media/agilex/Getea1/jiaan/data/motion/poses/home_poses.yaml 是现场位姿唯一来源，configs/home_poses.example.yaml 仅供参考，runtime/ 保存 ROS/相机/机械臂日志。网页保留同名轻量转发脚本。

前臂、中臂、后臂和示教交接节点均纳入 robot/arms。ROS 消息／Astra 驱动和 Piper SDK 是现场安装依赖，不属于旧 cobot-platform 业务目录。源码来源见 [HARDWARE_SOURCE](docs/HARDWARE_SOURCE.md)。

完整命令与故障恢复见同级 cobot-web/docs/COMMAND_LINE.md；RLT 操作见同级 rl-platform/docs/RUNBOOK.md。归位参数与此前一致，例如 scripts/home.sh selected --targets mid,front-right --pose plug2；执行前核对选中的机械臂和位姿。
