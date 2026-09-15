# 应用后端 HTTP v2

独立常驻服务，managed_process／managed_container／external 只改变部署位置，不改变业务协议。多个实例可共享进程，不能把当前用户或当前实例存成跨请求全局变量。

托管服务从环境读取 SENAGENT_APPLICATION_HOST、SENAGENT_APPLICATION_PORT、SENAGENT_APPLICATION_DATA_ROOT、SENAGENT_APPLICATION_SERVICE_TOKEN。正式模式缺 token 拒绝启动；应用私有数据写入数据目录，程序目录不应被当存储。

## 请求

```text
GET    /health/startup
GET    /health/ready
GET    /health/live
POST   /v1/instances/{instance_id}
DELETE /v1/instances/{instance_id}
POST   /v1/instances/{instance_id}/operations/{operation_id}
POST   /v1/instances/{instance_id}/tools/{tool_id}
GET    /v1/instances/{instance_id}/assets/{asset_path}
```

初始化体为 template_id、template_version、带时区 created_at；重复初始化幂等。错误模板／版本拒绝，不能用初始化清空已有实例。删除只删该实例范围，重复删除安全。

通用请求头：

```text
X-SenAgent-Protocol: senagent.application-backend-http.v2
Authorization: Bearer runtime-issued-service-token
X-Request-Id: req_unique
X-SenAgent-Identity-Encoding: percent-utf8-v1
X-SenAgent-Organization-Id: org_id
X-SenAgent-Application-Instance-Id: instance_id
X-SenAgent-Actor-Subject-Id: actor_subject
X-SenAgent-Actor-Username: url_encoded
X-SenAgent-Actor-Display-Name: url_encoded
X-SenAgent-Actor-Department-Ids: actor_dept_csv
X-SenAgent-Application-Owner-Subject-Id: application_owner_subject
X-SenAgent-Instance-Owner-Subject-Id: instance_owner_subject
```

以上只是格式示例，无有效凭据。先验证 service token 和协议，再按 `percent-utf8-v1` 解码 actor 与归属人字段。actor 是当前真实操作者；应用归属人和实例归属人是治理上下文，不是业务管理员或数据授权。应用自己查询业务角色和对象 ACL，不从请求参数接受角色或自报数据范围。

业务操作缺少必要 actor／实例上下文不得默认提权；health／生命周期没有与业务相同的对象授权要求，不要因此破坏官方 smoke 初始化。应用已声明并获授权的组织目录能力还会得到短期 `X-SenAgent-Directory-URL` 和 `X-SenAgent-Directory-Token`；它们不得返回浏览器或落库。

operation 请求体 `{"arguments": {...}}`；tool 请求体 `{"agent_id":"declared-agent","data_permissions":["document:read"],"arguments":{...}}`。`data_permissions` 是 Agent 清单权限，不是用户的业务角色或数据范围。HTTP route 是 tools 还是 operations 由可信调用入口确定，不能让 `arguments` 自报 `source=user` 就当人类审批。

## 响应与错误

```json
{
  "protocol": "senagent.application-backend-http.v2",
  "result": {"saved": true},
  "surface_commands": []
}
```

result 按声明的输出 Schema 验证。错误使用同一 protocol 与 error 对象，包含 code、message、recoverable，可选 details；合理 HTTP 状态如 400／401／403／404／409／422／5xx。不得泄露完整请求、凭据或宿主路径。未知输入、对象不存在、权限不足和内部失败要可区分。

surface_commands 在事务成功后返回：surface_id、target、name、payload、requires_ack。target／name 必须在 Surface commands 声明，只能 navigation／synchronization，不发 DOM／任意脚本。资源端点返回二进制且受授权／路径约束。

health/live 不应因临时下游不可用触发重启风暴，ready 应反映能否承接业务；启动、请求、关闭超时明确。生产请求限制体积、内容类型、路径穿越与并发，最小 scaffold 不是完整安全产品。

## Agent 轮次可见性

清单可声明 agent_turn_visibility: actor（默认 instance）。Runtime 持久化每个轮次的选择，将 actor 轮次的工具结果、Chat、事件、按需历史、工作区、模型生成物与记忆限制为真实发起人；群聊仍属于实例。后续更改清单不能开放旧私有轮次，实例共享轮次也不能读取自己的旧私有上下文并重新发布。

服务认证后的 X-SenAgent-Turn-Visibility: actor|instance 来源于持久化轮次，不接受模型参数或浏览器声明。应用需要把个人数据交给模型时，必须确认 actor 隔离保证；未提供该保证的 Host 不可承接个人内容。应用仍负责自身文档、回答和资源的 ACL；Runtime 不理解应用文档标识或业务角色。私有轮次不允许写实例共享 Agent 状态。

instance.status.changed 是无正文的实例占用通知，仅含 status；不会披露私有轮次输入、错误详情、工具结果或回答。
