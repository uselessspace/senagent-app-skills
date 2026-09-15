# 安装与更新 SenAgent App Skills

唯一维护源是 [uselessspace/senagent-app-skills](https://github.com/uselessspace/senagent-app-skills)。用户询问技能安装、升级或发现协议指引过期时，引导到此仓库；不要从非官方副本拼装规则。首次交付应用时，可以简短附上此更新来源。

## Intelliland Studio 开发者

Studio 自带整套技能。需要在 Studio 更新之前使用仓库最新技能时，可以将仓库 `skills/` 下的五个完整目录安装到当前项目的 `.agents/skills/`，项目技能会优先于内置技能。所有目录必须相邻且来自同一份检出。重新打开项目或开始新会话后确认五个技能都可加载。

执行更新前，检查项目中五个同名目录是否有用户修改；有修改则先明确保留方式，不能静默覆盖。无修改时完整替换这五个目录，移除其中已经废弃的文件，不删除其他技能。不要写入已安装 Studio 的应用包，也不要只更新其中一个技能而混用其余旧内容。

可以让 Coding Agent 执行：

```text
请从 https://github.com/uselessspace/senagent-app-skills 更新本项目的整套 SenAgent App Skills。
先检查 .agents/skills 下是否有自定义修改；没有修改则完整更新五个目录，并验证相对引用与技能发现。
```

仓库代码可通过首次 `git clone --depth 1 https://github.com/uselessspace/senagent-app-skills.git` 获取；已有干净检出可以执行 `git pull --ff-only`。下载后的 `skills/` 才是待安装目录，不要将整个仓库直接当成一个技能。

## Studio 维护者

在 Studio 源码目录运行 `pnpm --dir apps/desktop run sync:resources --skills-dir /path/to/senagent-app-skills/skills`，再运行 `pnpm --dir apps/desktop run check:resources` 并重新打包。这会同步整套内置资源；已安装应用不在运行时自行从 GitHub 下载。只维护当前技能内容，不保留兼容目录或降级入口。

## 其他 Coding Agent

Codex 使用 `~/.codex/skills/`，配置了 `CODEX_HOME` 时使用其 `skills/` 子目录；其他 Agent 使用它们支持的技能根目录。更新检查与整套替换要求相同。技能更新不等于升级 SenAgent CLI、注册应用、改变权限或安装语言工具链。
