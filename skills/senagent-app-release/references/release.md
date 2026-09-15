# 应用制品发布与安装核验

## 前提

应用清单只用 v4、Python／Go、backend HTTP v2；只使用最新 CLI／Runtime 的公开协议，缺少必需能力时要求更新，不提供旧版兼容路径。应用业务测试、权限与删除确认、必要 Chat／Surface 测试已有证据；真实模型没测应明确限制。

先准备独立 CLI 并核对帮助；当前独立安装渠道尚未交付，缺失就记录阻塞，不要求用户取得 Runtime 源码。此处目标指已部署的 SenAgent 服务，本机和内网服务器采用同一应用制品/API 边界，不访问开发者电脑目录。

目标部署由用户管理，不创建 dev/prod 配置体系。可信开发机完成构建、full 和业务测试；Runtime 注册阶段只校验候选结构、摘要和安装后的后端就绪状态，不执行候选构建命令。容器发布必须携带已构建且按摘要固定的镜像；目标主机不需要应用构建工具链。

## 仅打包

以下命令中的路径、仓库与 URL 是示范，必须替换成用户明确指定值：

```bash
senagent app package /work/apps/my-app \
  --output /work/releases/my-app-0.1.0.sapp --format json
```

命令 full 验证并检查内容摘要；制品是用户应用 Agent／前后端／资源工程，不含 SenAgent 私有源码。不要原地覆盖已发布包；新版本新输出。普通 package 不自动容器化。

检查密钥、Token、.env、私钥、真实业务数据、私有路径和不必要开发产物；.env.example 也必须没有真实值。官方归档过滤不是完整秘密扫描。输出不能放源目录引发摘要漂移，打包期间停止并发改源码。

## OCI：含仓库写入

```bash
senagent app package /work/apps/my-app \
  --output /work/releases/my-app-0.1.0-oci.sapp \
  --oci-repository registry.example.com/team/my-app \
  --oci-platform linux/amd64 --oci-platform linux/arm64 --format json
```

先确认仓库、架构、费用／网络和推送授权。需要 Docker／buildx 和仓库认证。审阅实际 Dockerfile 的依赖锁安装、资源复制、迁移、证书、cgo 和非 root 数据目录权限；脚手架不自动推导新增业务资源。

结果 manifest 固定 image@sha256。源码、开发摘要、生产摘要、镜像 digest、archive SHA-256 分别记录，不能混为一个摘要。multiarch 构建不是每种架构运行通过。当前 OCI 构建取工作树，需防并发修改；不要宣称已具备不可变构建来源证明。

OCI .sapp 只引用仓库镜像，不包含离线镜像全集；私有目标需仓库可达／镜像导入方案。构建和验收可能运行应用代码，不要对未经审查第三方包在高权限宿主执行。

## 上传与启用分开确认

```bash
senagent app publish /work/releases/my-app-0.1.0-oci.sapp \
  --runtime https://senagent.example.com \
  --access-token-file /run/secrets/senagent-user-token --format json
```

IAM v2 首次上传会提交平台审核。展示目标、当前用户权限、ID／版本、对象摘要、替换／权限／数据影响。默认敏感操作需要确认；一次明确批准可以覆盖已展示且完全未变更的步骤，不重复索取同一确认，不把“写代码”当批准。

平台管理员审阅摘要后使用 Studio 或 `senagent app approve <candidate-id> --digest <digest> --revision <revision> --runtime <url> --access-token-file <file>` 批准首次注册。已有应用使用 `app publish --update`，要求归属人或应用管理员身份，无需重复人工审核。发布失败先检查原候选和发布记录，不把重新上传视为原请求重试。内容变化需重新提交；`--activate` 已移除。

发布用用户访问凭据，不用模型 SDK Key。凭据文件 owner-only、不在应用目录、避免 shell history／日志。CLI 读文件不等于自动强制其权限位。

检查退出码和结果：即使 --format json，错误可能为文本 FAIL；不能解析失败后拿旧包继续。取消／无回应不上传或启用；失效 token 报告身份问题，不轮换部署 Key。

## 安装核验与交接

核对目标公开状态中的应用版本／摘要、注册启用状态和后端就绪；不以上传成功或 HTTP 200 代替。执行中或等待选择的实例不能被强制覆盖；安装失败时查明当前生效版本。业务迁移由应用负责，回退代码不等于恢复业务数据。

交付目标 URL、应用 ID／版本、源码／制品／镜像／安装摘要、候选或审批标识、启用结果与恢复限制，不包含凭据。输出区分 packaged／staged／activated；只有实际安装证据才可标 activated。

运行验收唯一维护于 [Verify](../../senagent-app-verify/SKILL.md)。完整 Builder 流程须继续目标验收；用户单独只要求打包或注册时在该阶段结束，明确运行验收尚未完成，不自动执行模型、业务写入或浏览器操作。
