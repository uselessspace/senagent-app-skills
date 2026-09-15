---
name: senagent-app-builder
description: 从需求到交付创建或迭代 SenAgent AI 原生应用；负责需求澄清、Python／Go 选型、前后端与 Agent 实现，并组织 CLI、审查、验证和发布。仅审查、仅验证、仅 CLI 或仅发布使用对应专项 Skill。
---

# SenAgent 应用构建总入口

用户只需描述应用目标。负责需求、实现和完整交付；专项操作按需读取同套 Skill，不要求用户逐一调用，也不意味着启动多个 Agent。

## 安装与任务范围

五个 `senagent-app-*` 目录必须在同一 Skill 根目录下完整安装。公共开发规则与当前协议由本 Skill 维护，其他 Skill 用相对路径引用，不复制规则。不维护兼容记录、旧版路径或降级分支。缺文件先报告安装不完整，不能用旧指令补齐。

用户只要求审查时转到 [Review](../senagent-app-review/SKILL.md)，只验证转到 [Verify](../senagent-app-verify/SKILL.md)，只开发 CLI 转到 [CLI](../senagent-app-cli/SKILL.md)，只发布转到 [Release](../senagent-app-release/SKILL.md)。专项任务完成不等于应用整体通过，也不自动扩大为完整开发或部署。

## 需求与计划

1. 读取 [规划与语言选型](references/planning.md) 和已有工程，识别新建或迭代，保留现有代码与明确偏好。只问影响方案且尚未明确的信息。
2. 新建时必须询问是否需要外部系统、脚本或 Coding Agent 调用应用。需要时按 [CLI 范围确认](../senagent-app-cli/references/external-cli.md) 展示具体能力、身份、权限和 CLI 交付方案，获得明确范围后同步构建；未回答保持待确认。迭代时仅复核范围变化，已确认内容不重复问。
3. 尽早明确目标 SenAgent、注册身份、测试实例／数据范围与模型预算。完整交付的最低证据见 [目标验收](../senagent-app-verify/references/target-smoke.md)。未知目标不默认选生产环境；用户明确只做本地时尊重范围。
4. 在 `APPLICATION_DESIGN.md` 记录需求、决策、范围和验收计划。该记录属于应用设计，不新增 Runtime manifest 字段。

## 实现

先执行 `senagent --version`、`senagent app --help`，核对 [当前协议](references/protocols.md)。缺独立 CLI 时报告依赖阻塞，可继续设计和不依赖 CLI 的实现，不要求开发者获取 Runtime 源码。

新建使用 `senagent app scaffold ABSOLUTE_ROOT --id APP_ID --language python|go`，不得覆盖非空目录。按语言指导对齐工具链后，用 Verify 建立脚手架基线，再增量实现业务；已有应用不重新 scaffold。

只加载本次所需参考：

- Python：[Python 工程](references/python.md)；Go：[Go 工程](references/go.md)，优先与开发者本机工具链一致。
- Agent／应用内 Skill／工具／模型：[职责与能力](references/agents-and-models.md)。
- HTTP 后端：[HTTP 契约](references/backend-http.md)。
- 身份、共享、个人内容和持久化：[身份与数据](references/identity-and-data.md)。
- 敏感操作或 Chat：[确认与历史](references/confirmation-and-chat.md)。
- 业务前端：[Surface](references/surface.md)；无需求不建前端。
- 需要设计实例时：[应用经验](references/application-patterns.md)，只参考模式。

业务前后端、Agent、应用内 Skill、依赖、迁移和测试留在应用工程。双方只通过公开协议交互，不导入 Runtime 内部包、不直读其数据库或私有目录。技术默认值由规划和语言参考维护，不重复维护另一套。

## 组织专项工作

| 时机 | 加载 | 输入与交付 |
| --- | --- | --- |
| 外部调用范围确认后 | [CLI](../senagent-app-cli/SKILL.md) | 已确认能力与应用路径 → CLI、说明与命令测试 |
| 新增能力前及实现完成后 | [Review](../senagent-app-review/SKILL.md) | 需求、设计、实际代码 → 职责与业务问题清单；修复仍由 Builder 负责 |
| 脚手架基线及业务实现后 | [Verify](../senagent-app-verify/SKILL.md) | 同一版本应用与验收计划 → 本地构建／业务证据 |
| 本地必要检查通过且发布已授权 | [Release](../senagent-app-release/SKILL.md) | 制品、目标与授权 → 注册启用状态及安装摘要 |
| 注册启用后 | [Verify](../senagent-app-verify/SKILL.md) | 安装摘要、测试身份与范围 → 后端、Agent／模型、前端与约定 CLI 的真实验收 |

交接沿用已有答案和证据，传递应用绝对路径、版本／摘要、已确认范围、未解决问题和报告位置；不复制凭据值。专项 Skill 不再调用 Builder 启动同一流程。失败回到相应实现环节修复，内容改变后重新生成相关证据，不拼接不同版本的通过结果。

## 完成判定

[交付阶段](references/workflow.md) 定义阶段名称；Verify 的 [目标验收](../senagent-app-verify/references/target-smoke.md) 是最低运行证据的唯一维护位置。Builder 汇总 Review、Verify、Release 和适用 CLI 的结果，默认须已注册启用并满足全部适用验收才能说整体通过。

用户只要本地或某专项时，仅报告该范围完成及未运行阶段。目标、权限、审批、工具或关键证据缺失时明确阻塞，不能放宽门槛。敏感操作沿用已确认且未变化的范围；缺授权不执行。连续两轮同类修复没有新证据时报告原因，不循环尝试或扩权。
