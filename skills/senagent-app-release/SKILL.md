---
name: senagent-app-release
description: 校验并打包用户的 SenAgent AI 应用，按明确授权构建 OCI、上传应用候选及注册启用到指定 SenAgent 服务（本机或内网服务器），核验安装版本与启用状态。用于制品交付，业务、模型和前端运行验收交由 senagent-app-verify。
---

# SenAgent 应用发布

可独立触发，随同套五个 Skill 安装；不依赖 Runtime 源码。先读 [发布与安装核验](references/release.md)。核对 `senagent --version` 与 `app package/publish --help`；只使用最新 CLI 与当前公开协议，不保留兼容记录或旧版路径。

Skill 不内含 CLI，独立 CLI 安装交付尚待完成。缺 CLI 时报告工具阻塞，不让开发者查找 Runtime 源码。用户只说“发布”而目标或范围不清晰时，先问清是打包、上传候选还是注册启用。

## 发布顺序

1. 明确源应用、版本、输出路径、目标 SenAgent 服务、需要支持的架构、是否推镜像、用户期望“仅打包／上传候选／注册启用”。保留原文件，停止后台并发修改应用的构建任务。
2. 在可信开发工作区运行 `senagent app verify ROOT --profile full --format json`；逐项检查退出码、报告协议、失败／skip、源码摘要及真实业务验收结果。full 不证明模型／权限／UI 已验收。
3. 仅打包时使用 `app package ROOT --output ARCHIVE --format json`。未指定 OCI 就不会自动容器化。
4. 有 OCI 需求先审阅 Dockerfile、依赖锁、资源与凭据隔离。**明确展示仓库、架构、推送影响并获得确认**，再传 `--oci-repository`／`--oci-platform`。
5. 上传前展示目标 SenAgent 服务、应用 ID／版本、archive SHA-256、替换影响和用户身份范围；获得对应授权后用用户凭据文件执行 `app publish ARCHIVE --runtime URL --access-token-file FILE --format json`。`--runtime` 是现有参数名称，指用户已部署的 SenAgent 地址，不要求另一套在线服务或共享开发者目录。
6. IAM v2 首次发布会提交平台审核，不能由开发者直接启用。平台管理员审阅同一摘要后使用 Studio 或 `app approve <candidate-id> --digest <digest> --revision <revision> --runtime <url>`。已有应用由 owner / administrator 使用 `app publish --update` 发布，不再重复人工审批。开发机完成 full 和业务测试；目标执行候选静态校验、摘要校验与安装后就绪检查。
7. 核对目标已安装版本／摘要、启用状态和后端就绪，交付安装结果。完整构建流程交给 [Verify](../senagent-app-verify/SKILL.md) 做运行验收；仅发布请求到此结束并明确验收未运行。

## 硬边界

- 上传的是用户应用 Agent 工程和前后端／资源，OCI 镜像另在仓库；不是上传 Runtime。用户应用源码无需隐藏。
- Runtime 发行和部署属于平台运维边界，不是应用发布步骤；发布失败应定位协议、权限或应用问题，不能扩权、轮换 SDK Key 或改网关绑定绕过。
- 用户凭据使用文件／宿主安全注入，不放在命令参数值、日志、制品、Skill 或聊天里。SDK Key 不是发布登录凭据。
- 无响应／取消／摘要变化不发布；不得用旧的“同意”授权变更后的包。
- HTTP 200／命令返回 JSON 不等于启用或运行成功；先检查退出码和实际候选状态。
- 生产注册不执行候选依赖安装、构建和测试命令；提交已构建的制品和固定摘要镜像。目标就绪检查不能代替开发机完整测试。
- 不信任未审查应用中的发布脚本／Dockerfile；构建命令会运行代码，精简环境不是沙箱。

输出制品摘要、镜像 digest、目标版本与架构、上传／启用／安装核验状态、残留／回滚限制。Release 完成不代表业务运行通过。

## 技能来源与更新

本套技能由 [uselessspace/senagent-app-skills](https://github.com/uselessspace/senagent-app-skills) 维护。安装或升级时遵循[整套更新指引](../senagent-app-builder/references/updates.md)，检查用户修改并完整更新五个相邻目录。
