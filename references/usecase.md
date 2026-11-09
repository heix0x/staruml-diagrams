# 用例图（kind: usecase）

**状态：verified** — 视图结构抄自本机 `test3-修正版.mdj`（同版本 StarUML 打开过）。

## 描述文件

```yaml
diagram:
  kind: usecase
  name: 银行储蓄系统-用例图
module: 场景视图

elements:
  - {id: cust,  kind: actor,   text: 客户, side: left}
  - {id: staff, kind: actor,   text: 工作人员, side: right}
  - {id: open,  kind: usecase, text: 开户}
  - {id: pwd,   kind: usecase, text: 设置密码}

relations:
  - {from: cust, to: open, kind: association}
  - {from: open, to: pwd,  kind: include}
```

### 元素

| kind | 说明 | 额外字段 |
|---|---|---|
| `actor` | 参与者（小人） | `side: left / right`，决定站左边还是右边，默认 left |
| `usecase` | 用例（椭圆），**默认类型** | 无 |

`text` 是显示的名字。id 可以和 text 不同，长名字用 id 会好写。

### 关系

| kind | 画出来 | 实现 |
|---|---|---|
| `association` | 实线、无箭头 | `UMLAssociation` + `UMLAssociationView` |
| `include` | 虚线箭头 + «include» | `UMLDependency` 带 name，**不是** `UMLInclude` |
| `extend` | 虚线箭头 + «extend» | 同上 |

`include` / `extend` 用 `UMLDependency` 是为了稳：`UMLInclude` 的字段是 `addition` / `includingCase`，写错不报错但线不显示；`UMLDependency` 的 `source` / `target` 语义明确，视觉上完全一样。

## 结构

模型层：`UMLModel` → `UMLUseCaseDiagram` + `UMLActor` / `UMLUseCase` / `UMLDependency`。

视图层：

| 视图 | 必需字段 |
|---|---|
| `UMLActorView` | `subViews: [UMLNameCompartmentView]`、`nameCompartment`、`containerChangeable: true` |
| `UMLUseCaseView` | 名称栏 + 4 个隐藏 compartment（attribute / operation / reception / templateParameter） |
| `UMLAssociationView` | `head` / `tail`（视图 id）、`points` |
| `UMLDependencyView` | 同上，带 `nameLabel.text = "«include»"` |

用例的 `UMLNameCompartmentView` 要放在椭圆中心附近：`y + h/2 - 12`。

## 布局规则

- 用例按 4 列网格铺开（`COLS = 4`），行距 40、列距 46。
- 左侧参与者放在用例区左边，纵向均分；右侧同理。
- 参与者连用例：从角色中心水平拉到椭圆边缘。
- 用例之间：同行连左右边，跨行走上下边。

元素少（≤6 个）时 4 列会显得空，可以调 `usecase.py` 里的 `COLS`。

## 坑

1. **参与者不能当普通节点画。** 它必须是 `UMLActorView`，StarUML 才画小人。用矩形视图代替会变成方框。
2. **`side` 写错会重叠。** 两个 actor 都在 left 时，它们会分列排但挤在一起，跟用例区打架。
3. **「系统边界框」不要用 Package。** Package 的符号带文件夹标签页，且默认白色填充会盖住下面的用例。要用边界框，得用 `System Boundary` 元素并把它 `Send to Back`——脚本目前不生成边界框，需要的话在描述文件外手动加。
