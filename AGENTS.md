# 项目入口

先读 `/data/LFT-W02_data/jiaan/jiaan/agent-guide/AGENTS.md`，再读本项目 [README.md](README.md) 与 [迁移记录](docs/MIGRATION.md)。按用户当前任务执行，保留已有成果和其他对话的改动。

项目：cobot-control。目标：统一前后双臂独立控制、CAN、ROS、相机、示教按钮、控制权切换、归位与恢复。保留已验证的控制语义和现场操作方式。

当前已开始业务迁移，以 docs/MIGRATION.md 的具体验收／切换记录为准；不得把目录存在或源码 clone 视为运行验证。跨项目问题按项目说明交给对应领域，证据与进展写回所属项目。

## 2026-09-30 按项目接管与并行对话

这是长期项目入口，不再处于“仅初始化”阶段。先读最新记录并核对代码/运行状态；历史旧路径、PID 和未完成描述不能当作当前事实。

- 负责：CAN、ROS、相机、设备启动停止/身份、示教按钮、前后臂同步、控制权、归位、Recover、位姿与硬件健康。
- 深入阅读：README.md、docs/DEPLOYMENT.md、docs/HARDWARE_SOURCE.md、docs/MIGRATION.md。
- 实现入口：src/cobot_control/、robot/arms/、scripts/control.py、scripts/can_diagnose.py、configs/；web 硬件脚本多数为兼容转发。
- 当前事实：硬件规则已下沉，网页与终端共用；可诊断新增 CAN drop、持续 TX 堵塞/排空。TX 卡死根因尚未锁定，无人值守自动 CAN 重置未启用。
- 下一步：复现定位 gs_usb/TX 停滞，区分 BUS-OFF 自动 restart 和发送队列卡死；先保留证据，再做有前置条件、单路隔离、可回退的恢复。继续验证中臂冷启动及示教退出。
- 边界：健康判定与物理恢复只维护一份，web 展示并调用。模型时序交 RL/VLA，mask 交 dagger。恢复/重启可能影响控制权，先核对现场。

用户会在同一项目开多个终端/对话并 fork。fork 不隔离工作树、GPU、端口、模型、Replay 或机器人。

1. 接管先读 git status/diff、git worktree list、实际进程/录制状态及 /data/LFT-W02_data/jiaan/jiaan/scratch/cobot-control/coordination/ 下已有任务说明（存在时）。先说明范围和共享资源。仅要求“读取目录 MD，了解项目”时先汇报，不自动训练/重启或执行所有旧待办。
2. 并行任务各在上述 coordination 下维护一个可读主题名 MD，登记负责人/对话标识、时间、分支/worktree、基线提交、计划文件、GPU/端口/输出和状态；自己的说明自己更新，结束标记完成。临时协调信息不入业务 Git，有用结果写正式文档，不替别的任务认领/完成工作。
3. 调研默认只读；分析用独立输出/只读快照，不改生产 Replay/权重。并行代码改动用独立分支/worktree，放 scratch/cobot-control/<可读主题>/，先核对依赖根/环境，不为 worktree 改生产路径。不在别人工作树切分支、reset、clean、stash 或全量提交。
4. 同文件/接口交叉先明确归属，独立开发后审核合并和调用方；合并、push、发布串行。共享 main、环境和机器配置不是并行试验区。只提交本任务改动，不 force push，不静默覆盖；合并前重查远端及未提交变化。
5. Cobot 同时只有一个启停/部署负责人，跨项目共用 /data/LFT-W02_data/jiaan/jiaan/scratch/cobot-web/coordination/cobot-live.md 说明（存在时先读）。未明确接管时仅只读/离线工作，不因模型“暂停”就抢 GPU、重启服务或切数据目录。进程锁只提供互斥，不是运动授权；硬件重启/运动前核对现场条件。
6. 新算法、采样、RTC/异步/EMA/频率使用可选配置、独立实验输出及明确回退。研究可并行；生产模型默认/参数/Replay 修改与运行负责人协调。
7. A6000 开发验证、所属仓库提交 push 后按清单校验同步 Cobot；区分源码已同步与运行已切换。结果写所属项目及 guide/projects/cobot-control/README.md 事实摘要；不改 guide 治理、不提交/推送 guide Git。

主仓库 /data/LFT-W02_data/jiaan/jiaan/projects/cobot-control；现场副本 /home/agilex/jiaan/project/cobot-control。数据/权重通常引用 Getea1/jiaan/{data,model}，实际登记配置优先（如 NVMe Stage1 路径）；不擅自搬资产。
