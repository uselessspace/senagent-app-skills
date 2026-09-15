---
name: senagent-app-review
description: 审查 SenAgent 应用的业务逻辑、Agent 职责、工具权限、确认流程和数据一致性，给出源码位置与证据。用于独立代码审查或构建前后自审，不自动修改、发布或调用真实模型。
---

# SenAgent 应用审查

与同套五个 Skill 一起安装。公共开发规则在相邻 Builder，测试执行方法在 Verify；按需读取参考，不启动完整构建流程。

## 审查路径

1. 明确应用路径、用户需求和审查范围。读取 [逻辑与职责审查](references/self-review.md)，沿真实入口追踪到授权、数据提交和用户结果。
2. 涉及角色时读 Builder 的 [Agent 与模型](../senagent-app-builder/references/agents-and-models.md)；涉及共享或个人数据读 [身份与数据](../senagent-app-builder/references/identity-and-data.md)；敏感操作读 [确认规则](../senagent-app-builder/references/confirmation-and-chat.md)。只检查实际相关的能力。
3. 核对已有测试证据与当前代码是否一致。必要时运行范围内可信本地测试；不把审查请求当作注册、模型付费调用、故障注入生产或修改实现的授权。完整执行验收使用 Verify。
4. 报告具体发现，不用文件数量、角色数量或固定评分代替语义判断。没有发现也要说明范围、已检查证据和未验证部分。

## 完成判定

交付按严重程度排序的问题清单，包含位置、触发条件、影响、证据和修复方向。说明角色应拆分／合并／保留的理由。可以判定“本次审查完成”或“发现阻断问题”，不能仅凭审查宣布应用整体通过。独立请求默认不改源码；构建中的修复交回 Builder，然后重新审查受影响链路。

## 技能来源与更新

本套技能由 [uselessspace/senagent-app-skills](https://github.com/uselessspace/senagent-app-skills) 维护。安装或升级时遵循[整套更新指引](../senagent-app-builder/references/updates.md)，检查用户修改并完整更新五个相邻目录。
