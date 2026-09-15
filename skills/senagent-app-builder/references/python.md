# Python 应用：FastAPI 默认路线

## 工具和起步

默认使用 Python `>=3.12,<3.14`、uv、FastAPI、Uvicorn 和 Pydantic。FastAPI 负责 HTTP 路由与边界验证，业务不变量、授权、事务和错误语义留在独立业务模块。安装 SenAgent Runtime 不代表已为应用提供 Python／uv；不自动安装全局工具。

在新空目录使用 `senagent app scaffold ABSOLUTE_ROOT --id APP_ID --language python`，随后先运行官方 full。命令中的大写项要替换为实际值。保留 `pyproject.toml` 和 `uv.lock`，依赖及验证命令都由应用自己锁定。

在应用根执行：

```bash
uv sync --frozen
uv run --frozen python -m unittest discover -s tests
uv run --frozen python -m compileall -q backend
```

使用 pytest／ruff／mypy 时把它们纳入应用锁文件和验证入口。`backend.verification.command` 必须运行测试，`compileall` 只是构建检查。

## 持久化与框架例外

零业务表的协议脚手架不需要 ORM。一旦应用需要持久化业务对象，默认加入 SQLAlchemy 2 和 Alembic，从第一版表结构开始使用追加迁移，不用 `create_all` 或启动时猜测替代版本化迁移。

- 单机、单写入服务和小数据量使用 SQLite，数据库文件放在 `SENAGENT_APPLICATION_DATA_ROOT` 下。
- 持续并发写、多副本或需要独立数库服务时直接使用 PostgreSQL。
- 只实现当前选定的一种存储。切换数据库是有数据迁移的后续变更，不是预先建两套 repository。

只在已有 Django 团队，或明确需要 Django Admin、认证生态与完整 ORM 时选 Django。只在需要自行组装轻量 ASGI 原语且 FastAPI 的功能反而多余时选 Starlette。不列出或预装其他框架。

## 基础测试资产

把本 Skill 的 `assets/python/test_http_contract.py` 复制到新应用 `tests/`；它使用 loopback HTTP 和临时目录，检查 service token、协议／模板匹配、实例幂等与删除隔离、健康端点。

更换应用内部布局时只适配启动夹具，保留协议断言。不得引入 `senagent` 私有 import。根据实际业务补充授权、迁移、并发、取消／确认和恢复测试。

## 业务与容器

参数校验、事务和行级权限在后端完成。正式启动缺少 service token 必须失败；测试用明确 fixture token，不增加“空 token 表示开发模式”的旁路。

新增依赖后同时修改 Dockerfile，按 `uv.lock` 安装应用依赖及所需系统库，并复制迁移／字典／模板等资源。生产启动由 Uvicorn 加载 FastAPI 应用，继续以非 root 用户运行。

数据写入注入目录／明确配置的数据服务，不写模板目录。不要依赖 Runtime 或宿主私有 `.env`；验证器使用收敛环境，不会继承所有凭据。当前 Python verifier 检查 uv 实际选中的应用解释器版本，不能用 CLI 自身 Python 的版本代替。

## 本地使用

full 和应用测试均在开发者电脑执行，不注册应用。要在 SenAgent 中真实使用，后续需打包、上传候选并确认注册启用，见 [阶段说明](workflow.md)。
