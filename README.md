# SenAgent App Skills

帮助 Coding Agent 构建、审查、验证和发布独立的 SenAgent AI 原生应用。一个总入口，四个可独立触发的专项 Skill。

## 五个 Skill

| Skill | 何时使用 | 交付 |
| --- | --- | --- |
| [senagent-app-builder](skills/senagent-app-builder/SKILL.md) | 从需求新建或迭代应用 | 应用实现与完整交付结论 |
| [senagent-app-cli](skills/senagent-app-cli/SKILL.md) | 增加或修改外部调用及应用命令行 | 已确认范围内的 CLI、说明与命令测试 |
| [senagent-app-review](skills/senagent-app-review/SKILL.md) | 审查业务逻辑、Agent 职责和权限 | 有源码位置和证据的问题清单 |
| [senagent-app-verify](skills/senagent-app-verify/SKILL.md) | 本地测试或已注册应用的真实验收 | 分阶段的执行证据与结果 |
| [senagent-app-release](skills/senagent-app-release/SKILL.md) | 打包、上传、注册或更新应用 | 制品摘要与目标安装状态 |

用户只需调用 Builder，Coding Agent 按阶段加载专项指引，不需要用户逐个调用，也不要求启动多个 Agent。单独调用 Review 不修改应用或触发部署，Verify 不自动发布，Release 的安装成功不等于业务运行验收通过。

## 安装

```bash
git clone https://github.com/uselessspace/senagent-app-skills.git
cd senagent-app-skills
```

将 `skills/` 下五个完整目录一起放到 `~/.codex/skills/`。设置了 `CODEX_HOME` 时使用其 `skills/` 子目录。五个目录必须保持相邻，因为专项 Skill 按相对路径读取公共规则和资产；可以独立触发，但需要整套安装。

更新前检查已有目录是否包含自定义修改，处理冲突后完整替换本套五个同名目录，避免旧文件残留；不要把其他 Skill 删除。其他 Coding Agent 使用其支持的 Skill 根目录，并保持五个目录相邻。

只维护最新协议与指引，不保留旧版入口、兼容记录或降级分支。安装不会安装 SenAgent CLI、启动 Runtime、开放权限或生成凭据。

## 使用示例

```text
使用 $senagent-app-builder，帮我开发一个资料归档 AI 应用。
使用 $senagent-app-cli，给这个应用增加 CLI，先确认开放哪些能力。
使用 $senagent-app-review，检查这个应用的 Agent 职责与权限，不改代码。
使用 $senagent-app-verify，验证这个已注册应用的前后端最小业务链。
使用 $senagent-app-release，把这个应用发布到我指定的 SenAgent 服务。
```

外部调用必须先确认能力、权限和 CLI 交付范围；需要时与应用同步实现。Go 工具链优先与开发者本机实际安装版本一致。

Builder 默认整体通过要求应用已注册启用，并完成全部适用的最低真实验收：后端业务、Agent／模型完成结果、前端关键操作及约定 CLI。缺目标、权限或证据时报告阻塞。用户明确只要本地或某专项时只完成该范围，不自动扩大授权。

## 依赖与内容归属

开发者需另行安装最新 SenAgent CLI 和选用的 Python／Go、按需前端工具链。先运行 `senagent --version` 和 `senagent app --help`；不要求获取 Runtime 源码。

- Builder 维护规划、语言、HTTP／Surface、身份／确认和当前公开 Schema。
- CLI 维护外部调用与命令交付规则。
- Review 维护语义审查方法。
- Verify 维护测试协议用法、验证脚本、测试资产和运行验收门槛。
- Release 维护打包、审批、发布及安装核验。

本仓库不包含 Runtime、CLI 二进制、工具链或真实凭据。Skill 自身校验不代表某个应用已通过业务或目标验收。

## Intelliland Studio 与后续更新

官方更新来源为 [uselessspace/senagent-app-skills](https://github.com/uselessspace/senagent-app-skills)。Studio 默认内置整套技能；需要提前更新时，可将本仓库 `skills/` 下五个完整目录安装到项目 `.agents/skills/`，优先于内置版本。不要修改已安装应用包。更新前检查自定义修改，完整替换本套目录以清除旧文件，保留其他技能；重新打开项目或开始新会话后确认技能加载。

Studio 维护者从最新检出同步到源码中的内置资源：

```sh
git pull --ff-only
# 在 Studio 源码根目录执行，路径指向本仓库的 skills 子目录。
pnpm --dir apps/desktop run sync:resources --skills-dir /path/to/senagent-app-skills/skills
pnpm --dir apps/desktop run check:resources
```

再按目标平台重新打包 Studio。详见[安装与更新](skills/senagent-app-builder/references/updates.md)。
