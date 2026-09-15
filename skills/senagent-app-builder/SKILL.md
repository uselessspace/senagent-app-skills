---
name: senagent-app-builder
description: 创建、修改、验证或审查独立的 SenAgent AI 原生应用；澄清需求、选择 Python 或 Go，确认外部调用与配套 CLI 范围，检查业务逻辑、Agent 职责划分、权限与真实测试证据。
---

# SenAgent 应用开发

用户只需描述想做的应用。主动完成需求澄清、选型、实现和验证引导，交付独立应用工程与实际证据；默认整体通过必须包含目标注册启用及注册后的最小真实验证，不能以生成文件或 `full` 通过代替业务完成。

## 开始

1. 识别新建、迭代或诊断，保留用户现有代码。先读 [规划与语言选型](references/planning.md)：关键信息不清晰时先追问、确认理解，再推荐 Python／Go；信息足够则给出依据并推进。用户明确选了语言就尊重，不要求用户在提示词中重复要求选型。
   新建应用必须询问是否需要外部系统、脚本或 Coding Agent 调用应用后端能力；已明确回答则复用。需要时，按 [外部调用与应用 CLI](references/external-cli.md) 逐项确认能力和 CLI 交付范围，在构建应用时同步实现并验收 CLI。未答复不视为“不需要”，范围未确认不开放接口或生成 CLI，可继续无关工作。迭代时核对新增能力是否改变已确认范围。
   同时尽早确认目标 SenAgent、注册权限、测试身份和最小验证的数据／模型预算，按 [注册后最小验收](references/target-smoke.md) 推进；未知目标不默认选择生产环境。
2. 读取 [使用流程与验证边界](references/workflow.md)，说明本次做到哪一步。使用独立 CLI 的 `senagent --version`、`senagent app --help`，按 [公开协议](references/protocols.md) 核对能力。缺 CLI 时明确报告依赖缺失，可继续澄清需求和设计；不能引导开发者查找 Runtime 源码或以源码工程路径代替安装。
3. 设计写入、删除、覆盖、清空、发布、权限修改或外部发送之前，必须读取 [确认与 Chat](references/confirmation-and-chat.md)。**敏感操作默认要求用户明确确认；模型参数不能充当人类确认凭证。**
4. 新增或修改业务能力前，以及宣告完成前，读取并执行 [逻辑与职责自审](references/self-review.md)。纯审查请求只给发现和证据，不擅自改实现。检查真实入口、Agent／Skill、后端与数据状态，不能只看清单或让作者自述代替代码。
5. 根据任务只加载所需参考：
   - Python：[Python 工程](references/python.md)；Go：[Go 工程](references/go.md)。
   - 角色／工具／能力：[Agent 与模型](references/agents-and-models.md)。
   - 外部系统／脚本／Coding Agent 调用、配套命令行：[外部调用与应用 CLI](references/external-cli.md)。
   - 共享、成员、组织／部门、持久化：[身份与数据](references/identity-and-data.md)。
   - 业务界面：[Surface](references/surface.md)。
   - 整体交付必读：[注册后最小验收](references/target-smoke.md)。
   - 需要理解真实产品拆分：[两个应用的经验](references/application-patterns.md)，仅参考模式，不复制业务。

## 默认技术路线

- 无既有团队约束时，Python 默认 FastAPI + Uvicorn + Pydantic；出现真实业务持久化后再加 SQLAlchemy 2 + Alembic。只有强后台／完整 ORM 需求或团队已用 Django 时选 Django；只有明确的轻量 ASGI 底层需求时选 Starlette。
- Go 默认 Gin；出现真实业务持久化后再加 GORM。
- 单机、单写入服务和小数据量默认 SQLite；持续并发写、多副本或需要独立数据库服务时选 PostgreSQL。一个版本只实现一种存储，不为未来可能切换预建双适配层。
- 需要持久业务界面时默认 React + TypeScript + Vite。有服务端缓存与失效需求才加 TanStack Query，有多页路由才加 TanStack Router，需要可访问的复用组件时再用 shadcn/ui。没有业务界面就保持 `surfaces: []`。

## 实现与验证

- 新建用官方 `senagent app scaffold ABSOLUTE_ROOT --id APP_ID --language python|go`；不得覆盖非空工作区。先跑原始脚手架建立基线，再增量加入业务和测试。已有应用不重新 scaffold 覆盖。
- 业务后端／前端、Agent／应用内 Skill、依赖、迁移、测试均在应用工程。SenAgent 集成只依赖公开的版本化协议，Runtime 私有实现不是开发依赖；源码保护和程序写权限由发行／部署机制保证，不依赖提示词约束。
- Agent 白名单分别配置模型逻辑能力、Runtime 工具、backend tools、数据权限、委派目标。Skill 不拥有独立权限，不能绕过模型策略或后端授权。
- 删除等敏感操作先解析稳定对象和影响范围，再 `request_choice`；取消／超时／无回应不执行，范围或版本变化重新确认。普通读取不增加确认负担。
- 涉及个人数据先确定 `agent_turn_visibility`，读取 [身份与数据](references/identity-and-data.md) 和 [HTTP 契约](references/backend-http.md)；实例共享关系不能自动开放个人上下文。
- 供应商 Key 只由独立模型网关持有；Runtime SDK Key 与当前用户凭据只进入 Runtime 网关适配器；应用后端只信任已验证 service token 的请求中的 actor、应用归属人和实例归属人上下文。业务角色与对象 ACL 由应用自己持久化；原始当前用户凭据不下发应用。
- 按 [验证与排障](references/verification.md) 运行官方分层验证、配套测试、业务正反例及按需 UI／模型测试。修复失败原因，不删测试、扩权或伪造通过。
- 必须按 [应用测试协议](references/application-tests.md) 运行 `senagent app test`，执行语言原生测试与业务 suite，检查必要用例、退出码和未运行覆盖。CLI 缺少该命令是安装／版本阻塞，不能用 full 冒充业务完成。
- 完成后再审一次实际改动及其调用方：需求是否闭环、角色划分是否内聚、权限／确认／失败恢复是否可达。自审结论与工具结果分别记录；存在未解决的关键逻辑问题时不能宣称整体完成。
- 实现敏感操作测试时读取[确认断言接入](references/confirmation-testing.md)，复用 Python／Go 断言并连接真实业务状态；框架自测、交互确认与强审批证据分别报告。
- 需要本地构建与后端启动门禁时执行 `scripts/verify_app.py`；其使用 Python 3.12+、支持 macOS/Linux，调用 full，不代表完整业务或 SenAgent 服务联调验收。脚本路径相对本 Skill 目录，应用路径必须明确。
- 报告通过／失败／未运行／阻塞项、命令与退出码、摘要、工具链、尚需的模型绑定／目标安装。应用没有 Surface 可记不适用；缺测试工具不可记通过。

## 停止与交付

遇到缺授权、付费调用未获授权、协议无能力、目标不明确或破坏性范围不清，提出一个明确问题；不自行改环境、安装全局软件或轮换凭据。连续两轮同类修复没有新证据时，报告阻塞而不是循环尝试。

默认开发交付包括工程校验、业务测试、目标注册启用及一轮最小真实验收，按 [注册后最小验收](references/target-smoke.md) 判定。缺目标、权限、首次注册审批或验证能力时，交付已有工程并标记对应阻塞，不宣称整体通过。用户明确仅要本地开发／禁止部署时尊重范围，只报告本地阶段完成、整体验收未运行。不要要求用户重复提示才执行已授权的注册后验收。

执行默认交付中的打包、上传候选或注册启用时，使用已明确的目标和授权，可调用另行安装的 `senagent-app-release`，逐项确认目标、内容和相应操作；只说“发布”且范围不明确时先澄清。该 Skill 不可用时按注册后最小验收中的当前 CLI／公开协议继续；必需能力或权限缺失则报告阻塞，不猜命令。Skill 更新替换同名安装副本，只使用当前版本，不要求用户挑选多个版本。

## 组织目录接入

新建和更新应用只使用 `senagent.application-manifest.v4`。涉及组织、部门或人员时，读取 [公开协议](references/protocols.md) 的组织目录段，并执行 [验证与排障](references/verification.md) 的目录验收项。目录读取授权与应用自有业务数据权限必须分开。
