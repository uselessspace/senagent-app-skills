# 可执行确认断言：接应用，不冒充 Runtime 协议

Python 资产：[confirmation_contract.py](../assets/python/confirmation_contract.py)。
Go 资产：[confirmationcontract/contract.go](../assets/go/confirmationcontract/contract.go)。
两种语言都提供9个相同含义的应用适配器契约测试，只依赖各自标准库。
它们不是审批功能实现，也不会给业务工具签发任何凭证；不提供新的 SenAgent API。

## 什么时候使用

应用有不可逆操作，且已实现自己的预览／确认／提交路径时，连接该路径及真实数据查询。
没有敏感操作则记录不适用理由，不给最小脚手架硬加删除业务。
应用目前只有直接删除 API、没有范围／版本／幂等机制时，测试会暴露缺口；不要在测试适配器里补一个假确认服务让测试通过。
强审批要求仍见[确认与 Chat](confirmation-and-chat.md)，不能因为本测试通过就承诺模型不可绕过。

## 适配器边界

每个用例创建独立、可安全销毁的 fixture：至少一个待操作对象和一个应保留的旁观对象，预览仅选择前者。
对象 ID 和版本映射到测试结构，不规定应用必须采用某种数据库或 API 字段。
工厂创建失败时也负责清理已创建资源；正常路径由框架调用 close／Close。

| 方法 | 必须连接的真实行为 |
| --- | --- |
| snapshot／Snapshot | 读取 fixture 的持久化对象 ID→版本，以及已提交破坏性操作数量 effects；不能从上次响应推算状态 |
| preview／Preview | 调用应用只读预览，返回稳定计划 ID 和目标快照；预览不能改业务对象 |
| respond／Respond | 将测试选择映射到应用真实控制器／HTTP／UI提交路径，包括非法选择；不能自己决定是否调用删除，以掩盖被测代码缺陷 |
| revise／Revise | 真正修改目标对象版本，模拟确认前并发编辑 |
| fail_next_commit／FailNextCommit | 在真实提交边界注入确定性失败；故障不能先修改业务数据，失败后要读取真实状态验证无部分写入 |
| close／Close | 只清理工厂自建的精确资源；清理失败必须报错，不能 catch 后吞掉 |

测试结构中的 Plan、Snapshot、Outcome 和 selections 是**测试适配接口**，不是待发送的 Runtime 请求 Schema。
稳定选择名称为 confirm_delete／cancel_delete，适配器转换成当前应用实际选项 ID。
Outcome.status 为 pending／cancelled／rejected／failed／succeeded；成功返回可查询的 operation_id。
effects 是实际提交操作数，用于发现重复副作用，不是 HTTP 请求数；没有此观测能力时应补应用自有审计或测试观测接口，不能硬编码为1。
读取业务状态失败必须让测试失败，不能转换成“空数据＝删除成功”。

## Python 接入

把资产复制为应用 `tests/confirmation_contract.py`，编写 `tests/confirmation_adapter.py` 实现工厂。
新增 `tests/test_confirmation.py`：

```python
import unittest
from confirmation_contract import ConfirmationContract
from confirmation_adapter import create_driver

class ConfirmationTests(ConfirmationContract, unittest.TestCase):
    def create_driver(self):
        return create_driver()
```

`create_driver` 必须实现上述真实适配，不能直接实例化 Protocol。缺适配器必须失败。
沿用脚手架的 unittest 结果适配器；也可为 confirmation suite 单独使用只发现该文件的结果适配器。
必要用例 ID 前缀为 `test_confirmation.ConfirmationTests.test_`，后缀见下面表格中的场景 ID，将 `-` 改为 `_`。
Python 方法 `valid-exact-confirm` 对应 `test_valid_exact_confirm`。

## Go 接入

复制资产到应用 `backend/internal/confirmationcontract/contract.go`；应用测试包新增：

```go
func TestConfirmation(t *testing.T) {
    confirmationcontract.Run(t, newConfirmationDriver)
}
```

导入当前工程 module 下的 `backend/internal/confirmationcontract`，不要导入示例 module 或 SenAgent。
`newConfirmationDriver(t *testing.T) confirmationcontract.Driver` 在应用测试包实现，失败用 t.Fatal，不返回伪造成功。
使用脚手架原生 Go 结果适配器；必要用例 ID 为 `实际module/实际测试包/TestConfirmation/场景ID`。
工厂早期资源可用 `t.Cleanup` 清理；Close 不得删除同测试 fixture 以外的数据。

## 用 app test 执行

在 `application.tests.json` 声明 `category: "confirmation"` 的 suite，command 指向本语言结果适配器，
required_cases 列出选定入口适用的9个测试 ID，再运行：

```bash
senagent app test /absolute/my-app --suite confirmation --format json
```

只复制资产文件不会自动注册测试：Python 必须有 TestCase 子类，Go 必须有 Test 开头的入口。
不要删 required_cases 或跳过失败用例来获得通过。报告必须说明实际被测路径，未连接真实路径只算测试框架自测。
同一 suite 可以发现附带的契约测试，但不能把仅有契约用例的 suite 改名为 confirmation 冒充确认覆盖。

## 19条规格的实际覆盖

以下是框架可执行的**本地适配器级断言**，不是已替每个用户应用执行过的验收。

| 场景 ID | 当前断言／限制 |
| --- | --- |
| cancel | 返回取消，持久化数据及 effects 均不变 |
| no-response | 空回应不执行；真实超时、关窗、SSE 等待仍需各入口集成测试 |
| free-text | 自由输入不能直接提交；不验证真实模型对文本的理解 |
| multiple-options | 确认加取消、多项或未知选项拒绝且零副作用 |
| changed-targets | 追加旁观对象后计划拒绝；替换／移除及更多范围变体需应用补测 |
| changed-version | 实际修改版本后旧计划拒绝，修改后的数据保持不变 |
| duplicate-submit | 首次精确执行，重复返回原 operation_id 或拒绝，提交数不增加 |
| backend-failure | 确定性提交失败，状态为失败且零部分写入；响应丢失后的查询／恢复仍需补测 |
| valid-exact-confirm | 只移除选中对象，旁观对象版本不变，effects 恰好加1 |

其余10条尚无本框架驱动：different-actor、different-instance、clear-snapshot、revoked-permission、expired-plan、
cancel-race、model-forged-confirmed、prompt-injection、empty-preview、surface-dismiss。
需要应用授权／时间／并发／可信入口／浏览器适配后单独补测，不将其视为跳过后整体通过。
尤其不同主体、伪造 confirmed 和提示注入必须沿真实信任边界测试，不能靠一个本地布尔参数证明。

当前维护者测试使用临时磁盘对象作为框架自测 fixture，分别故意注入10种错误并通过真实 `app test` 检测失败。
这些 fixture 不进入 Skill 包，不是用户应用实现，更不是已验证了现有两个业务应用。
真实 Chat 事件、Surface 行为、UI 成功消息、授权撤回和强审批端到端均不在此通过结论内。
