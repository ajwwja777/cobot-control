# Cobot 硬件与独立前后双臂控制

统一前后双臂独立控制、CAN、ROS、相机、示教按钮、控制权切换、归位与恢复。保留已验证的控制语义和现场操作方式。

## 入口与位置

- 先读统一框架：`/data/LFT-W02_data/jiaan/jiaan/agent-guide/AGENTS.md`。
- A6000 主工作区：`/data/LFT-W02_data/jiaan/jiaan/projects/cobot-control`。
- 笔记本对话入口：`D:\Code\jiaan_workspace\cobot-control`。
- 自有独立仓库：`https://github.com/ajwwja777/cobot-control`（目标分支 `main`）。
- Cobot 目标部署位置：`/home/agilex/jiaan/project/cobot-control`，本轮尚未部署。
- 当前阶段：入口与仓库初始化；旧业务代码、环境、模型和数据尚未迁移，现有服务入口未切换。

## 负责什么

设备发现与状态、硬件启动停止、控制权与示教状态、选择臂和位姿的归位／恢复、底层相机接口。

向采集、VLA、RL 和网页提供设备接口；数据标签与训练 mask 交给 cobot-dagger，模型动作语义交给 vla-platform，运行编排与日志交给 cobot-ops。物理设备控制权必须统一，调用方不得另起绕过仲裁的控制链路。

## 机器与资产

A6000 负责主代码、Git、维护文档、主要开发验证环境、数据处理和离线评测；训练按资源需要在 A6000／已授权训练机进行。Cobot 只部署本项目现场实际需要的硬件、采集、推理、网页或维护组件，不复制仿真资产和完整训练环境。

Cobot 采集及评测数据统一规划在 `/home/agilex/jiaan/data/`。模型放所属项目的 `models/`（上游已有 `checkpoints/` 等目录时保留其源码布局，由配置明确实际权重位置）；同一资产跨项目引用，避免重复复制。现场服务日志、PID 和状态交由 `cobot-ops/runtime/` 管理；训练 checkpoint、配置和指标保留在所属项目 `outputs/<实验>/`。环境、模型、大数据与 runtime 不入 Git。

## 项目协作

CAN、反馈、相机和归位问题由本项目负责；服务存活、PID 与磁盘问题先交 cobot-ops；模型输出异常交 vla-platform。

先读本次任务涉及的依赖项目入口和接口说明，再修改相关边界；接口变更要记录受影响调用方与验证方式。常用项目：`cobot-control`、`cobot-dagger`、`vla-platform`、`rl-platform`、`cobot-web`、`cobot-ops`，主工作区均在 `/data/LFT-W02_data/jiaan/jiaan/projects/`。需要专题对话时仍共享所属项目，不因此重复建立业务仓库。

## 下一步

选择一个可隔离的设备状态查询入口，核清依赖后复制到新位置，比较新旧状态语义和错误处理；第一批不改变运动逻辑。

旧位置、验收条件和切换／清理规则见迁移记录。

来源：2026-09-27 用户确认的项目划分、机器职责与逐批迁移方案；本轮范围仅初始化。
