# SenAgent CLI 选择与更新

## 确认正在使用哪个 CLI

| 工具 | 用途 | 入口 |
| --- | --- | --- |
| SenAgent 完整开发 CLI | 应用验证、测试、打包、发布和外部调用 | 独立安装的 `senagent`，以实际 `--help` 为准 |
| Intelliland Studio 内嵌 CLI | 发布已有制品、使用个人凭据调用应用 | Host 提供的绝对路径 `"$SENAGENT_CLI"`；仅 `app publish` 和 `client` |
| 应用专属 CLI | 某个应用开放的业务命令 | 由该应用交付说明指定 |

这些工具与 Codex CLI、模型网关的管理工具分别维护。本技能仓库只提供开发指引，更新技能不会更新任何 CLI 可执行文件。

在 Studio 中先检查 `test -x "${SENAGENT_CLI:-}" && "$SENAGENT_CLI" --version`，变量存在时使用该入口，不用 PATH 中另一个同名程序替代。需要 verify／package 时转到具备完整 CLI 的可信开发工作区；Studio 内嵌 CLI 随 Studio 发行更新。

## 更新完整开发 CLI

从 SenAgent 维护者取得当前开发 wheel、对应 SHA-256、依赖约束文件和 `install-development-cli.sh`。本仓库没有 CLI 下载资产，不把技能目录当安装包，也不要求应用开发者获取 Runtime 源码。安装命令中的路径和摘要必须替换为实际交付值：

```bash
bash /path/to/install-development-cli.sh \
  /path/to/senagent-VERSION-py3-none-any.whl \
  EXPECTED_SHA256 /path/to/constraints.txt
```

安装器先验证摘要，再通过 `uv tool install` 安装。约束文件用于锁定依赖，不应包含指向旧 wheel 的 SenAgent 自身条目。安装后使用安装器输出的可执行文件绝对路径，在源码目录之外、未设置 `PYTHONPATH`／`PYTHONHOME` 的环境检查 `--version`、`app verify --help`、`app package --help` 和 `app publish --help`。

记录实际 wheel 的 SHA-256 和交付方提供的构建标识。同一版本号可能对应重新构建的包，仅看到 `0.4.1` 不能证明已安装本次修复；以交付包摘要和安装结果核验。

## macOS 验证进程清理

当前开发 CLI 已修复 macOS 上已退出、尚未回收的 Docker 子进程导致 `smoke.process-cleanup` 误报的问题：清理过程先回收子进程，并在权限错误时进行有时限的退出检查，同时保留进程组残留检查。

遇到该症状时，先核对安装包是否包含修复，再按报告检查本次资源并重新运行 smoke 和最终 full／package。权限错误也可能代表真实残留，不能仅凭错误文字认定误报、跳过清理或改写失败报告。恢复规则见 [验证失败处理](../../senagent-app-verify/references/verification.md)。
