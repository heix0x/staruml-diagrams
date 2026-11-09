# 时序图（kind: sequence）

**状态：verified** — 结构经 StarUML 实际打开验证通过（办理读者证 / 借书 两张时序图，含守卫条件分支与生命线自适应间距）。

## 描述文件

```yaml
diagram:
  kind: sequence
  name: 取款时序图
module: 进程视图

elements:
  - {id: c,   kind: lifeline, text: 客户,     represent: actor}
  - {id: s,   kind: lifeline, text: 工作人员, represent: actor}
  - {id: sys, kind: lifeline, text: 系统}

relations:
  - {from: c, to: s, text: 输入密码()}
  - {from: s, to: sys, text: 请求验证账户()}
```

### 元素

| 字段 | 说明 |
|---|---|
| `text` | 生命线顶部的名字 |
| `represent: actor` | 画成参与者小人；不给就是普通矩形 |

生命线等距铺开，间距至少 220px。

### 关系

| 字段 | 说明 |
|---|---|
| `from` / `to` | 生命线 id |
| `text` | 消息名（序号由 StarUML 自动加，格式是 `1: 消息名`） |
| `reply: true` | 可选，画成虚线返回箭头 |

消息按数组顺序从上往下排，间距 42px。

## 结构（两条硬约束）

### 1. 消息视图的 `head` / `tail` 指向 **linePart**，不是生命线视图

`UMLSeqMessageView.update()` 里判断的是 `this.head instanceof UMLLinePartView`。指向生命线视图的话，消息不会吸附到生命线中心，激活条也不会出现。

```
UMLSeqLifelineView
├── UMLNameCompartmentView     名字
└── UMLLinePartView            ← 虚线本身，消息连这个
```

### 2. 激活条的显示条件

三者同时成立才显示：

```
head 是 UMLLinePartView
showActivation: true
messageSort ∈ {synchCall, asynchCall, deleteMessage}
```

激活条的坐标由 `UMLActivationView.arrangeObject()` **自动算**：`top` 取消息终点 y，`left` 取 linePart 左边再左移半个宽度。写进 mdj 的值会被覆盖，只需保证存在且 `visible: true`。

高度默认 `ACTIVATION_MINHEIGHT`，会自动扩展到包住子激活；**只增不减**。脚本给的高度是 41（比消息间距小 1），这样相邻激活条首尾几乎相接，看起来是一条连续长条。

### 3. 模型层三层嵌套

```
UMLInteraction
├── messages:     [UMLMessage]          内嵌
└── participants: [UMLMessageEndpoint]  内嵌
        └── represent → UMLActor         小人靠这个
```

`UMLMessage` 有 `source` / `target` 指向 participant，`messageSort` 默认 `synchCall`。消息显示的文字来自 `name`（没有 `signature` 时）。

## 坑

1. **不写 `showActivation: true` 就没有激活条。** 而且它写在 `UMLSequenceDiagram` 上，不是视图上。
2. **`head` 指向错层级是最常见的错。** 症状：消息线悬空在生命线旁边，或者激活条全挤在顶部。
3. **消息序号格式改不了。** StarUML 固定输出 `1: 消息名`，教材上常见的 `1.消息名` 做不到，除非把序号写进消息名（然后会被再加一遍）。
4. **组合片段（alt / loop）没实现。** 需要的话得加 `UMLCombinedFragment` + `UMLInteractionOperand`，结构比消息还复杂一层。
5. 消息的 `points` 只需两个点，x 会被 `arrangeObject()` 按激活条重新算，y 保持不变。
