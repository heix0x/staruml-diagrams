# 构件图（kind: component）

**状态：derived** — 结构按 `elements.js` 里的 `UMLComponentView` 定义推导，未在 StarUML 打开验证。首次使用必须开图确认，确认后把 `scripts/component.py` 和本文顶部的 STATUS 改成 `verified`。

## 描述文件

```yaml
diagram:
  kind: component
  name: 银行储蓄系统-构件图
module: 开发视图

elements:
  - {id: main, kind: component, text: 主程序构件, at: [80, 240]}
  - {id: bank, kind: component, text: 银行构件,   at: [430, 60]}

relations:
  - {from: main, to: bank}
```

### 元素

| 字段 | 说明 |
|---|---|
| `text` | 构件名，显示在框内 |
| `at: [x, y]` | 可选。不给就排两列网格 |
| 宽高 | 自动，按名字长度算（最小 160×80） |

### 关系

| kind | 画出来 |
|---|---|
| `dependency`（默认） | 虚线箭头，从使用方指向被依赖方 |

## 结构

模型层：`UMLModel` → `UMLComponentDiagram` + `UMLComponent` + `UMLDependency`。

视图层 `UMLComponentView` 和类视图同构，要五个 compartment：

```
nameCompartment / attributeCompartment / operationCompartment
receptionCompartment / templateParameterCompartment
```

后四个 `visible:false`，但**必须存在**——缺了 StarUML 会把构件框画成没有分隔线的裸框。

## 坑

1. `UMLComponent` 和 `UMLComponentInstance` 不是一个东西。前者是类型，后者是对象图实例。构件图只能用前者。
2. `containerChangeable: true` 要带上，否则不能把构件拖进节点里。
3. 依赖箭头方向：**使用方 → 被依赖方**。画反了语义全错，而且视觉上看不出来。
