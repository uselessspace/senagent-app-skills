---
name: senagent-app-verify
description: 验证 SenAgent 应用的本地构建、业务测试和已注册目标的真实运行，检查后端、Agent／模型、前端及应用 CLI，汇总可核验结果。用于验收或测试失败定位，不自动发布、扩权或修改业务实现。
---

# SenAgent 应用验证

与同套五个 Skill 一起安装。读取 [验证方法](references/verification.md)，根据请求选择本地验证、目标验证或完整验收；只验证某阶段时不自动扩展成发布。只使用最新 CLI／公开协议，缺少必需能力就报告阻塞。

## 本地验证

确认应用路径、当前版本与测试范围，读取 [应用测试协议](references/application-tests.md)，运行适用的 `app verify` 与 `app test`，检查必要项、退出码和未运行覆盖。需要受控输出／进程门禁时使用本 Skill 的 `scripts/verify_app.py`。失败先保留证据和定位原因，不删测试、扩权或伪造成功。

敏感操作按需读取 [确认断言接入](references/confirmation-testing.md)，将本 Skill 的 assets 接到真实应用入口和状态。框架自测不是业务测试。涉及组织目录、个人轮次、连续对话或 CLI 时执行验证方法中对应检查。

## 已注册目标验证

读取 [注册后最小验收](references/target-smoke.md)。接收 Release 的安装版本／摘要以及已授权测试身份和数据／模型范围，再执行真实验证。未注册的应用不能通过目标验收；需要注册时报告前置条件，由已授权的 Release 阶段完成，本 Skill 不自行发布。

平台 CLI、公开 API 与浏览器分别用于其能证明的部分。不能把 action 受理当 Agent 完成，不能把 HTTP 200 当前端可用；没有 Surface 才可将前端验收记为不适用。

## 证据与完成

报告每阶段通过／失败／未运行／阻塞／不适用（理由），附应用及安装摘要、命令、退出码、业务断言、目标结果和资源收尾状态；凭据不入报告。报告置于应用树外。

仅本地验证通过时明确尚无目标证据。完整验收须满足目标验收的全部适用项及需求中的其他必要检查。验证证据不代替 Review 的业务设计审查；最终应用整体交付由 Builder 汇总。独立验证可以在请求范围内完成，不自动调用其他 Skill 扩大任务。

## 技能来源与更新

本套技能由 [uselessspace/senagent-app-skills](https://github.com/uselessspace/senagent-app-skills) 维护。安装或升级时遵循[整套更新指引](../senagent-app-builder/references/updates.md)，检查用户修改并完整更新五个相邻目录。
