# 应用测试协议与执行

开发必须使用当前 CLI 的 `senagent app test`，先执行 `senagent app test --help` 核对参数。缺少该命令是 CLI 安装／版本阻塞，不能把 `full` 当成业务测试替代品，也不要求开发者获取 Runtime 源码。

## 执行与验收

```bash
senagent app test /absolute/my-app --format json --cache-dir /absolute/app-test-cache
senagent app test /absolute/my-app --suite backend-contract --format json
```

缓存、报告必须位于应用树外。0 表示所选 suite 通过，1 表示失败，2 表示参数错误。
`--suite` 可重复；省略时运行所有声明项。选择部分 suite 即便退出0，也必须查看未选项和 coverage。
四类 coverage 为 contract／business／confirmation／surface；未声明或未选中的覆盖不能记通过。
`build_and_startup`、`live_model`、`target_installation` 始终是 not_run；这些证据由其他实际验收提供。

新脚手架已包含语言原生结果适配器：Python `scripts/run_tests.py` 调用 unittest，Go `tools/testreport`
调用 `go test -count=1 -json ./backend/...`。后者不需要 Python。两者只依赖标准库和公开测试协议，不导入 Runtime。
基础测试覆盖 health、生命周期幂等、错误响应、service token 与实例路径；不验证业务 actor／owner／ACL 规则或人类确认。

## 增加业务 suite

独立文件 `application.tests.json` 使用[测试计划 Schema](../../senagent-app-builder/assets/protocols/application-test-plan-v1.schema.json)，
不是 application.yaml 的新字段。每个 suite 声明唯一 id、category、command argv、working_directory（默认`.`）、
timeout_seconds（1–1800，默认300）、required_cases。工作目录不得绝对或越界；command 必须是数组，不拼 shell 字符串。

为真实业务增加数据准备、动作、结果读取、断言和清理；例如删除应断言取消后记录仍在，确认后才消失。
拆分测试时让各 suite 的命令只发现对应测试目录／包，不把相同的契约测试换个 category 再运行就宣称业务完成。
Python 可以调整 discover 目录或编写第二个标准库适配器；Go 调整测试包路径。更新 required_cases 的稳定 ID，不能删用例来消除失败。
没有可执行业务适配器时如实记录 business／confirmation 未运行；19条确认规格本身不是已运行的测试。

执行器向每个 suite 提供：

| 环境变量 | 用途 |
| --- | --- |
| SENAGENT_TEST_RUN_ID | 本次调用随机标识 |
| SENAGENT_TEST_SUITE_ID | 当前 suite 标识 |
| SENAGENT_TEST_SOURCE_DIGEST | 被测试源码摘要 |
| SENAGENT_TEST_RESULT_PATH | 本次全新、位于源码外的 JSON 结果路径 |
| SENAGENT_TEST_WORK_DIR | 当前 suite 私有且初始为空的测试数据目录 |

适配器在结果路径写入[结果 Schema](../../senagent-app-builder/assets/protocols/application-test-result-v1.schema.json)：固定 protocol、上述三项标识和
`cases: [{"id": "稳定测试ID", "status": "passed|failed|skipped"}]`。case ID 必须符合 Schema，禁止把用户输入或凭据作为 ID。
suite 测试失败必须返回非零退出码；不能仅输出 PASS 字样，也不能复制历史 JSON。
Python 框架异常、失败 subtest、意外成功都应映射为失败；跳过／expected failure 不算通过。

CLI 同时核对进程退出码、报告标识、源码摘要、required_cases 和所有用例结果。零用例、全跳过、部分跳过、重复 ID、
结果缺失／超限／非法、测试期间改动源码、超时或进程泄漏都失败。
最终[报告 Schema](../../senagent-app-builder/assets/protocols/application-test-report-v1.schema.json)包含原始 source_digest、规范化 plan_digest、各 suite 错误码、
用例结果和私有 log_path。这些是本次执行证据，不是密码学证明；恶意应用代码可以伪造自报结果，业务断言仍需评审。

## 执行边界与排障

- 支持 macOS／Linux。每个 suite 使用独立源码副本、临时 HOME 和数据目录。源码变化后必须重新测试；生成 fixture、输出和依赖环境放在源码外。
- 使用工程锁文件；uv 可按锁文件下载依赖／Python，Go 固定本地工具链并禁止自动改 go.mod。不是断网执行承诺；内网工具链和依赖镜像预配另行处理。
- 不读取部署 Settings，不继承 Runtime Key、用户 Token 或其他原始环境。不自动登录、注册、发布或调用真实模型。
- 只执行开发者信任的测试代码：源码副本和精简环境不是操作系统／网络沙箱；代码仍具有当前 OS 用户权限，也可能读取本机文件。不要用真实密钥或生产数据作为 fixture。
- 进程组超时或残留时尝试清理；脱离进程组的 daemon／容器不能保证回收。cleanup_review_required 为 true 时检查本次资源，不能全局 kill 或 prune。
- 原始输出不进入 JSON，保存于权限受限目录。stdout／stderr 流式累计超过 16 MiB 时终止本次进程组，日志文件不会超过该上限。日志仍可能包含应用打印的敏感数据，查看／分享前脱敏。
- 缓存和日志暂不自动过期。只清理已确认属于本次调用的目录，不清空系统临时目录。

常见 suite code：tests.invalid_result（检查适配器和日志）、tests.result_mismatch（检查三项标识是否来自当前环境）、
tests.no_cases／tests.required_cases_missing（检查发现路径和必要用例）、tests.failed（修复断言或非零退出）、
tests.source_changed（移出测试生成物并检查并发编辑）、tests.timeout／tests.process_leak（检查测试资源清理）、
tests.output_limit（减少异常输出）、tests.toolchain_setup_failed（修复临时 Go telemetry 设置）、
tests.cleanup_failed（只核查本次进程组／容器）、tests.command_unavailable（核对工具链）。
