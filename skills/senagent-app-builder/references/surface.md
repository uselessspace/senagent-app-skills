# Surface 与 Chat 分工

Chat 属于 Runtime：消息历史、Markdown、流式输出、request_choice 和恢复都不重造。没有持久化业务 UI 需求时可以 surfaces=[]。

需要 Surface 时默认 React + TypeScript + Vite，使用 pnpm 锁定依赖，Vite `base` 设为 `./`，产物保留在应用模板内。只按需增加：

- TanStack Query：存在服务端状态缓存、失效和重试需求时。
- TanStack Router：存在多视图或可恢复深链时；静态入口默认用 hash history，不要求宿主配置应用路由回退。
- shadcn/ui：确实需要可访问的复用表单、对话框等组件时。

单视图用 React 本地状态和 `fetch` 就能完成时，不为技术栈对齐预装这些库。不引入第二套前端框架。

| 行为 | 入口 |
|---|---|
| 需要规划／理解 | actions → Agent Turn |
| 确定性保存、筛选、分页 | operations → 后端 |
| 确定参数的模型流水线 | capability_operations → prepare / Runtime 模型能力 / commit |
| 后端导航／刷新 | commands：稳定业务 ID，navigation／synchronization |

按钮不必都触发模型。请求只打开对象，不要额外生成分析。能力流水线校验对象、模型输出、权限变化和幂等；不能前端直连网关。

## 宿主接入

遵循随包 surface-host-v1 Schema。在一个小的 `SurfaceProvider` 中集中处理宿主握手、短期令牌和事件，业务组件不自己重复协议逻辑。独立 iframe 通过 `senagent.surface.ready` 与宿主上下文握手，校验 `event.source`、严格预期 origin、`channelNonce` 和实例／Surface 匹配；不使用任意消息里的 origin 建立信任，生产不使用 `*` 传递敏感上下文。

宿主 context 提供受限 surfaceAccessToken，不是用户完整登录 Token。独立打开可通过指定 Runtime 的 `/v1/surface-launch-codes/exchange` 交换 launch_code；按公开协议使用并从地址栏清掉短期 code。不要抄维护者机器的 baseURL。

目标完整 HTTP 客户端以匹配版本的 Runtime OpenAPI／公开 SDK 为准；本 Skill 没有内置万能 JS 客户端，Schema 未描述的路由不猜。缺目标 API 资料时只做离线界面，标记集成阻塞。

## 构建与敏感操作

`entry_path` 指向生产 HTML 及完整资源目录，不是 localhost 开发服务器。`development` 声明 `working_directory`、`install_command: [pnpm, install, --frozen-lockfile]`、包含类型检查的 `build_command` 和 `watch_paths`。提交 `pnpm-lock.yaml`；不用已有 `dist` 掩盖干净安装或构建失败。

删除／覆盖／发布／权限操作使用真实确认对话框：展示对象、数量、影响和可恢复性，取消优先，危险按钮不默认触发；Escape／关闭等于不执行，busy 时防重复提交。不能用倒计时确认。状态变更后重新读权威数据，失败不先乐观删掉唯一可见结果。

与 Chat 使用相同敏感操作策略，详见 [确认规则](confirmation-and-chat.md)。产品提供后台审批时两个入口共享同一计划／授权规则，不做两套互相绕过的删除逻辑。

测试实际浏览器：生产资源无缺失，身份过期、刷新／重连、空与错误状态、选择恢复、取消零写入、重复点击幂等、对象变化重新确认。已有 dist 被拷进构建快照可能掩盖 no-op build；在明确生成物范围内干净重建，不删除用户源码。
