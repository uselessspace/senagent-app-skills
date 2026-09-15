# SenAgent App Skills

帮助 Coding Agent 构建、验证和发布独立的 SenAgent AI 原生应用。

## 包含的 Skill

- [senagent-app-builder](skills/senagent-app-builder/SKILL.md)：需求澄清、Python／Go 选型、应用前后端与 Agent 开发、外部调用与配套 CLI 范围确认、业务测试、注册后最小真实验收。
- [senagent-app-release](skills/senagent-app-release/SKILL.md)：应用打包、OCI、上传候选、注册启用和目标安装验证。

只维护当前版本，使用最新 SenAgent CLI 和公开协议，不提供旧版兼容分支。本仓库包含 Skill、公开协议 Schema 和测试辅助资产；不包含 SenAgent Runtime、CLI 二进制或语言工具链。

## 安装到 Codex

克隆仓库：

```bash
git clone https://github.com/uselessspace/senagent-app-skills.git
cd senagent-app-skills
```

将 `skills/senagent-app-builder` 和 `skills/senagent-app-release` 两个完整目录放到 `~/.codex/skills/`。设置了 `CODEX_HOME` 时使用其 `skills/` 子目录。也可以只安装其中一个。更新时先检查本机是否有自定义修改，再替换同名目录，不并存旧版和新版。

其他 Coding Agent 可使用其支持的 Skill 目录或显式读取对应 `SKILL.md`。

## 使用

```text
使用 $senagent-app-builder，帮我开发一个资料归档应用。
```

Coding Agent 会确认业务范围、是否需要外部调用，以及需要同步交付的 CLI 能力。Go 工具链优先与开发者本机版本保持一致。

默认整体通过要求应用在指定 SenAgent 注册启用，并完成注册后最小真实验证。有前端时必须验证页面及关键操作；有 Agent／模型时必须检查真实完成结果。目标、权限或必要能力缺失应报告阻塞，不能把本地测试通过当成整体验收通过。用户明确只要本地工程时尊重该范围。

```text
使用 $senagent-app-release，把这个应用发布到我指定的 SenAgent 服务。
```

首次注册仍需平台管理员审批。发布前明确目标、制品摘要和操作范围；已经明确授权且内容未变时不重复确认。

## 前提

开发者需另行安装当前 SenAgent CLI，以及应用选用的 Python／Go 和按需前端工具链。先运行 `senagent --version` 和 `senagent app --help`。安装本仓库不会安装 CLI、启动 Runtime、开放权限或生成凭据；不要将真实凭据提交到应用工程或聊天中。

## 关键指引

- [外部调用与应用 CLI](skills/senagent-app-builder/references/external-cli.md)
- [注册后最小验收](skills/senagent-app-builder/references/target-smoke.md)
- [Go 工具链与工程](skills/senagent-app-builder/references/go.md)
- [公开协议](skills/senagent-app-builder/references/protocols.md)
