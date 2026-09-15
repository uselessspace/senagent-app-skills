# Go 应用：Gin 默认路线

## 工具和起步

默认使用开发者本机实际安装的 Go、Go Modules 和 Gin，不在 Skill 固定一个旧版本。Gin 负责 HTTP 路由与边界验证，业务不变量、授权、事务和错误语义留在独立业务包。有 cgo／架构限制时明确列出。模型质量不取决于后端用 Go。

先执行 `go version`、`command -v go` 和 `go env GOVERSION GOTOOLCHAIN GOOS GOARCH`，记录实际可执行文件、版本与平台。用户要求与本机一致时，以该机器检查到的完整版本为准，不自行升级、降级或安装第二套 Go；已有明确团队／部署版本约束时先说明冲突并确认。未安装 Go 时先确认目标版本与安装方式，不能凭 Skill 中的示例猜版本，也不自动安装全局软件。

在新空目录执行 `senagent app scaffold ABSOLUTE_ROOT --id APP_ID --language go`，先对齐下列工具链配置，再跑官方 full 建立基线，之后加入业务。保留 `go.mod` 和 `go.sum`，不依赖全局 GOPATH 或隐式工具链下载；verifier 使用 `GOTOOLCHAIN=local`。

## 将生成工程对齐本机

脚手架默认值不代表开发者的实际版本。生成后核对 `go.mod` 的 go／已有 toolchain 指令、`application.yaml` 的 Go 工具链约束、Dockerfile 构建镜像和已有 CI 配置。新应用按本机完整版本统一；清单要求精确一致时使用其支持的等值约束，不能仅保留旧的宽泛下限。不要为了本机验证新增容器或 CI，但已有配置必须一致。

`go.mod` 的 go 指令表示最低工具链要求，不单独保证精确版本；精确执行还需本地工具链、清单检查和容器／CI 固定版本共同保证。保留 `GOTOOLCHAIN=local`，不能靠自动下载另一版本掩盖不一致。修改 go 指令后核对依赖约束与 go.sum，不无故升级业务依赖。已有应用不机械改动版本，先核对用户要求及现有构建约束。

容器镜像标签须核实实际存在且适用目标架构，不能把本机版本拼成镜像名就宣称可用；无法取得匹配镜像时报告构建阻塞，不静默退回脚手架旧版本。使用宿主 CLI 的应用命令封装也应在同一工具链下构建和测试。

在应用根执行：

```bash
go mod download
go test ./...
go vet ./...
go build ./...
```

合适平台补 `go test -race ./...`，不把平台不支持记为通过。增加依赖后运行 `go mod tidy` 并提交锁定结果。

## 持久化

零业务表的协议脚手架不需要 ORM。一旦应用需要持久化业务对象，默认加入 GORM 和当前选定的一个数据库驱动。迁移用应用自有、追加的版本化文件；不用启动时 `AutoMigrate` 代替可审计迁移。

- 单机、单写入服务和小数据量使用 SQLite，数据库文件放在 `SENAGENT_APPLICATION_DATA_ROOT` 下。
- 持续并发写、多副本或需要独立数库服务时直接使用 PostgreSQL。
- 多副本的幂等键、写入冲突和业务状态必须通过数据库约束、事务与版本检查协调，不能依赖进程内 map／mutex；测试跨请求重试和并发写入。
- 不为未来可能切换同时维护 SQLite 和 PostgreSQL repository。达到升级条件时再做数据迁移。

## 测试和代码组织

保持 cmd 程序入口、Gin handler、业务服务／存储的边界；明确请求 context、关闭流程、超时和并发写入。handler 应可用 `httptest` 独立测试。

将 `assets/go/contract_test.go` 复制到 scaffold 的 `backend/internal/appserver/`，运行 go test。它通过 httptest 和临时目录验证 service token、协议／模板、幂等／删除范围；不包含 Runtime 私有 import。新业务包结构变化时适配测试夹具，不删行为断言。

迁移用追加文件，测试空库、旧库、重复初始化、失败恢复。业务操作与 Chat 确认规则和 Python 一致，语言不会自动提供权限隔离。

## 交付

生产构建二进制，不假定 Runtime 拥有 Go 工具链。OCI 打包时保证所有迁移、CA 证书、时区和资源用 embed 或 COPY 带齐；cgo 依赖和目标架构必须实际运行验收。

正式启动缺少 service token 必须失败；测试用明确 fixture token，不增加空 token 鉴权旁路。应用后端不能挂载 Runtime 源码／数据根或 Docker socket。

本地验证不注册应用；打包、上传候选与注册启用的边界见[阶段说明](workflow.md)。本文通用门禁脚本仍需 Python 3.12+；Go-only 开发者可直接运行官方 CLI 并审阅完整报告，Go 测试适配器不需要 Python。不谎称本包带了独立 Python 环境。
