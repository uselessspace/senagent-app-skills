# 公开协议

新建和更新应用只使用 `senagent.application-manifest.v4`，不生成旧 manifest，不在应用中增加协议猜测或兼容分支。CLI 与目标 Runtime 必须实际提供清单所声明的公开协议。

执行 `senagent --version`、`senagent app --help`；目标 Runtime 的 `GET /v1/protocols` 返回 schemas 名单，`GET /v1/protocols/{schema_name}` 返回 Schema。在线 fetch 不带无必要凭据、不把登录重定向当 Schema；离线用随包快照。禁止修改 Schema 放宽验证。

只使用最新 CLI 和当前协议 Schema，不维护兼容记录、版本矩阵、字段别名或旧版分支。协议名称相同不代表字段完全一致；目标缺少当前必需能力时明确要求更新，不能降级绕过。

随包文件在 `assets/protocols/`，由维护者从官方发行协议导出，不包含 Runtime 源码：

- application-manifest-v4.schema.json：新建和更新应用的唯一清单。
- application-backend-http-v2.schema.json：业务 HTTP 边界。
- runtime-event-v3.schema.json：事件；最终用户 Markdown 来自 message.completed。
- surface-host-v1.schema.json：独立界面的宿主消息。
- application-verification-report-v1.schema.json：full 报告。
- model-gateway-v1.schema.json：逻辑模型能力协议参考；应用不能据此直连网关。
- application-test-plan-v1.schema.json：应用声明的测试 suite 和必要用例。
- application-test-result-v1.schema.json：语言原生测试适配器的结果。
- application-test-report-v1.schema.json：CLI 业务测试执行报告与覆盖状态。

Schema 只描述它覆盖的数据，不等于全部 API 使用手册。后端行为读 [HTTP 契约](backend-http.md)，选择工具实际参数读 [Chat](confirmation-and-chat.md)，Surface 读 [界面](surface.md)。不要推断数据模型字段都可传给工具。

参数缺失／版本不支持应返回明确错误。协议没有可信确认凭证就声明缺口，不发明 `confirmation_required` manifest 字段或虚构一个 /approvals 端点。

通过 CLI 生成 scaffold 时只有 `python|go` 两种语言。不根据启动命令猜语言，不把某个框架的函数名当成 HTTP 协议要求。必须核对 CLI help 中的实际命令与参数。

组织目录能力使用 manifest v4 的 `organization_directory` 声明，并由平台在应用管理中单独授权。后端只使用当前可信调用中的短期目录能力；应用自定义业务角色和对象 ACL 保存在应用自己的数据库。

## 组织目录

平台应用治理接口仅供 Studio／CLI 管理使用，应用 Surface Token 不得调用。应用只通过组织目录能力读取已授权范围。

应用在 manifest v4 顶层声明 `organization_directory: {protocol: senagent.organization-directory.v1, operations: [departments, users]}`，只列实际需要的 `organization`、`departments` 或 `users`。声明不是授权：部署管理员还需配置目录读取范围。应用前端经清单声明的 Surface operation 调用自己的后端，后端使用本次可信请求的 `X-SenAgent-Directory-URL` 和 `X-SenAgent-Directory-Token`。URL 已是目录基路径，只追加 `/organization`、`/departments` 或 `/users`。

`/users` 支持 `query`、重复的 `subject_id`、`department_id`、`offset` 和 `limit`。部门返回数组；人员返回 `{items, next_offset}`，人员字段为 `subject_id`、`display_name`、`username`、`avatar_url`、`department_ids`，不含邮箱。

Token 仅留在后端，不下发浏览器、不落库、不写日志。HTTP 客户端设置超时并拒绝重定向；失效、撤权或跨范围请求必须失败，不能以更高权限凭据重试。

未获许可时 Runtime 不签发目录 capability；应用后端应将目录操作返回明确的 403，而不影响不使用目录的业务操作。目录故障应返回可识别的错误，前端显示失败并允许重试，不要转换成空部门／空成员。
