# 验证、调试和失败处理

先区分[验证与交付阶段](workflow.md)。本页的本地校验不上传候选、不注册启用应用，也不要求开发者电脑部署 SenAgent 服务。

## 官方层级

```bash
senagent app verify /absolute/my-app --profile static --format json
senagent app verify /absolute/my-app --profile build --format json
senagent app verify /absolute/my-app --profile smoke --format json
senagent app verify /absolute/my-app --profile full --format json
```

替换为实际应用路径。static 验结构；build 执行语言依赖／声明测试与构建、Surface 构建；smoke 启动、health、实例创建／幂等／删除／清理以及静态入口；full 组合 build 和 smoke。

报告 protocol 为 senagent.application-verification-report.v1。full 成功通常 achieved_level=runtime_ready，**不是 function_ready**。必要 check 缺失／skip、CLI 退出失败都不能通过。没有 Surface 的两个 Surface check 可以 skipped；有 Surface 而缺依赖不可以跳过。

非 static 的最终成功报告还须有 `verification.source-stable`：验证结束时重新检查应用摘要。先生成需要打包的产物并冻结源码；构建或启动若写入应用树导致摘要变化，应将可丢弃输出移到树外，或完成必要产物后重新验证，不能继续使用旧摘要作为证据。

## 配套门禁

从本 Skill 目录运行，报告写到应用树外的已存在目录，文件必须不存在：

```bash
python3 scripts/verify_app.py /absolute/my-app \
  --cli-json '["senagent"]' --report /absolute/reports/local-check.json
```

CLI 参数使用数组而不是 shell 字符串；若已安装的独立 CLI 不在 PATH，填可执行文件绝对路径。先检查 `app verify --help` 支持 `--cache-dir`；缺少所需 CLI 能力就报告工具阻塞，不通过 Runtime 源码工程调用替代安装。

有声明 Python build 时加 `--require-check build.python-artifact`；Surface editor 加 `--require-check build.surface.editor.production --require-check build.surface.editor.artifact`。从真实 manifest／验收计划推导必要项，不人为省略。

脚本对可信工作区运行真实 CLI，不主动调用模型或发布应用。脚本启动 CLI 时继承调用者环境，官方本地 verifier 再为应用构建与启动筛选环境；两者都不是操作系统或网络沙箱。不要在高权限环境运行不可信应用。CLI 的 stdout／stderr 合计超过 2 MB、超时或同进程组有残留都会失败并清理该组；原始输出不写入门禁报告。脱离进程组的 daemon／容器仍不能保证回收，出现 cleanup_review_required 时只核查本次资源，不全局 kill／docker prune。

`smoke.process-cleanup` 失败时，官方 verifier 会在该 check 中给出本次受限恢复目录；其中只保留脱敏日志、说明和可用的精确 CID 所有权证据。按该路径逐项处理后重新验证，不按容器名猜测归属，也不删除整个系统缓存或临时目录。

门禁在专用临时 cwd 中启动 CLI，并显式传入临时 `--cache-dir`，避免缓存进入应用目录造成摘要漂移。不会读取或切换已部署服务的环境。临时缓存和日志随退出清理，需深入诊断时用官方 verify 指定应用树外的 `--cache-dir` 重跑并保留脱敏报告；门禁输出中的临时日志路径在退出后不可用。不要把报告／缓存写回应用目录。

## 除 full 以外必需的证据

先完成[逻辑与职责自审](self-review.md)：工具结果与语义审查分别给结论，不能把 full 或合同测试通过当作 Agent 拆分合理的证据。

1. 业务：每个需求的正反例、持久化、事务、幂等、并发、重启／迁移。
2. 权限：错 token／伪造 actor、跨组织／部门／实例／对象、共享实例双主体和成员不继承。
3. 确认：[confirmation-cases.json](../assets/confirmation-cases.json)，包括绕过、取消、范围变更、重复、审批保证等级。
4. Chat／Agent：合法阶段、未授权工具拒绝、选择暂停／恢复、工具失败不宣告成功。固定模型夹具不等于真实模型结果。
5. Surface：干净生产 build + 浏览器资源／握手／操作／同步测试。
6. 模型：明确预算和授权后，少量真实调用检验能力绑定、模态／工具契约、质量与 actor／Agent 归因；connectivity check 不等于业务生成成功。
7. 目标：制品安装后不挂载源目录仍可创建实例和操作；多架构分别跑。未执行必须记未运行。

必须通过 CLI help 核对并运行 `app test`；命令缺失是 CLI 安装／版本阻塞。测试声明和执行见 [应用测试协议](application-tests.md)。没有通用 app e2e／mock-model 命令。集成驱动基于 SenAgent 公开 API，不读服务私表。

## 外部调用与个人数据验收

需要外部调用时执行 [CLI 验收](external-cli.md)，将命令级业务测试加入 `application.tests.json`，使用现有 business／confirmation 分类，不新增测试协议类别。缺真实个人凭据或目标服务时，报告客户端联调未运行，不用本地模拟替代。

涉及个人内容时执行 [轮次可见性验收](identity-and-data.md)：双用户同实例、权限撤回、私有轮次改配置后的历史保护，以及工作区／生成物／共享状态隔离。连续对话按 [历史规则](confirmation-and-chat.md) 测试。

## 整体通过门槛

本页工程与业务测试通过后，继续执行 [注册后最小验收](target-smoke.md)。注册启用、后端真实业务、适用的 Agent／模型与前端基础验证是整体通过的必要条件；app full、health、候选上传或 action 受理都不能替代。

## SenAgent 服务联调

按 CLI help 与目标服务实际提供的能力执行打包、上传候选、确认注册启用和服务内联调，每一步分开报告。目标服务不读取开发者工作区；目标安装验收使用部署者提供的验证环境，不把本地 full 冒充为已注册或真实 Chat 可用。

## 修复

缺工具报告需安装项与版本，不自动安装全局软件。build 检查锁文件／命令／资源；smoke 检查协议／service token／data root／ready／脱敏日志。模型失败检查绑定与授权，不向后端下发 SDK Key。容器失败核对 Dockerfile 依赖和 COPY，不能挂载整个开发机来“修复”。

连续两轮同类失败无新证据停止；不删测试、宽松 Schema、扩权、改 Key 或修改 Runtime 应用特判。修复后重跑受影响层及 full。

最终报告：应用／工具版本、命令与退出码、source_digest、各项通过／失败／未运行／不适用、敏感确认保证等级、模型调用预算与证据、目标安装限制、清理结果和启动说明。包内不存真实凭据。

## 组织目录应用适配必须验收

- 在真实部署的已安装版本中验证部门名称、部门选择和适用的人员搜索；旧数据的稳定部门 ID 与共享范围保持不变。
- 验证部门为空、请求加载中、服务故障、未授权／撤权分别显示；错误不能显示成“没有部门／没有成员”。失败时可重试，阻止依赖失败目录的权限保存，不把失败后的空数组写回业务数据。
- 验证普通应用使用者经 Surface operation 和应用后端读取目录，不能调用平台管理 API；跨组织／超出授权范围拒绝，目录 Token 不出现在浏览器响应和日志中。
- 检查应用源码与构建产物只通过清单声明的组织目录能力读取目录，再执行安装后的 UI 验收。只验证平台首页和实例能打开不算目录适配完成。

目录 capability 涉及应用后端回调 Runtime，必须在同一个真实 Runtime 中验证完整请求链。后端独立单测／启动检查无法发现宿主事件循环被同步 HTTP 调用阻塞造成的回调超时；遇到此问题应定位宿主调度，不增加应用管理凭据或绕过目录协议。
