---
name: senagent-app-cli
description: 为 SenAgent 应用新增或修改外部调用及配套 CLI；明确开放能力、调用身份、权限和命令范围，完成 CLI 实现与命令测试。用于已有应用 CLI 开发或 Builder 的专项阶段，不负责平台 CLI 开发与应用发布。
---

# SenAgent 应用 CLI

与同套五个 Skill 一起安装，公共协议和业务边界位于相邻 Builder。独立进入时先确定应用绝对路径、已有代码和用户要求；从 Builder 进入时复用已经确认的范围，不重新进行全量需求问卷。

## 范围与实现

1. 读取 [外部调用与 CLI](references/external-cli.md)，确认调用者、开放与排除能力、数据范围、敏感操作和交付方式。用户只说“支持外部调用”不足以开放全部能力；未明确的范围暂停实施，可继续不依赖答案的工作。
2. 核对 [公开协议](../senagent-app-builder/references/protocols.md) 和实际最新 CLI help。区分平台 `senagent client` 与应用自身 CLI；服务端必须落实权限，隐藏命令不等于禁止接口调用。
3. 按确认范围同步实现应用命令、公开请求映射、安装／使用说明和测试。后端业务规则留在应用后端，CLI 不导入 Runtime、不获得 service token、不复制业务授权。
4. 测试接入方法使用 Verify 的 [应用测试协议](../senagent-app-verify/references/application-tests.md)。本 Skill 执行命令级测试；完整应用与目标验收由 Verify 负责，不因此自行发布。

## 交付

逐项列出已确认能力 → 命令 → 后端入口 → 已执行测试，并标明排除项与阻塞。交付源码、安装入口、help、输出／退出码约定和测试证据。独立 CLI 开发只报告本次范围完成；来自 Builder 时返回结果供其汇总。真实目标调用必须已有身份、数据和模型预算授权，不因构建 CLI 自动获得授权。
