# 流程图（kind: flowchart）

**状态：verified** — 本机 StarUML 5.0.2 打开确认过（实训4 的两张流程图）。

StarUML 的流程图是独立扩展（`FCFlowchart`），不在 UML 包里。元素名都以 `FC` 开头。

## 描述文件

```yaml
diagram:
  kind: flowchart
  name: 素数判断流程图
module: 流程图

elements:
  - {id: start, kind: terminator, text: 开始}
  - {id: in, kind: data, text: 输入 n}
  - {id: deci, kind: decision, text: "i < n ?"}
  - {id: calc, kind: process, text: i ← 2}
  - {id: end, kind: terminator, text: 结束}

relations:
  - {from: start, to: in}
  - {from: deci, to: calc, label: 是}
  - {from: calc, to: deci, back: true}
```

### 元素

| kind | 画出来 | StarUML 模型 | 默认尺寸 |
|---|---|---|---|
| `terminator` | 圆头框 | `FCTerminator` | 100 × 44 |
| `process` | 矩形 | `FCProcess` | 170 × 50 |
| `decision` | 菱形 | `FCDecision` | 180 × 90 |
| `data` | 平行四边形 | `FCData` | 180 × 50 |

宽度会按文本自动加长。`text` 就是框里显示的字。

### 关系

| 字段 | 作用 |
|---|---|
| `from` / `to` | 元素 id |
| `label` | 线上的文字，`是`/`否` 这类 |
| `back: true` | 回边。**必须标**，否则会被当成正向边，rank 无限拉长，图变成一条长长的折线 |

## 结构（写脚本时对照）

模型层：

```
FCFlowchart
├── FCFlowchartDiagram      ownedViews
├── FCTerminator / FCProcess / FCDecision / FCData   各元素，name 是框里的字
│   └── FCFlow              ★ 连线挂在**源节点**的 ownedElements 下，不是在图上
└── ...
```

连线模型 `FCFlow` 有 `source` / `target`（模型 id）和 `name`（线上文字）。

视图层：

| 视图 | 关键字段 |
|---|---|
| `FCTerminatorView` 等 | `subViews` 里一个 `LabelView`；`nameLabel` 指向它；`wordWrap: false` |
| `FCFlowView` | `head` / `tail`（**视图 id**）、`lineStyle: 2`、`points`、`fillColor: "#ffffd8"` |

`FCFlowView` 的 `head` 指向目标视图、`tail` 指向源视图。

## 布局规则（脚本已实现）

1. 忽略 `back` 边算 rank（最长路径），同 rank 排同一行。
2. 列分配 BFS：能走到「结束」的那条出边留本列，其余开新列；标了「否 / else」的优先当主干。
3. 同列直连；跨列走折线；`back` 边从最左绕过，**垂直进入判断节点顶部**。

## 坑

1. **判断节点必须单入口。** 回边不要连菱形侧面，连顶部。侧插会让判断框有两个入口线，肉眼看着像 bug。
2. **菱形宽度要够。** `FCDecisionView` 的名称栏只占视图宽度的 1/2，文字长了会被挤。脚本按 `文本宽 × 2 + 50` 算，自己改代码时别缩这个系数。
3. **`back` 漏标是最常见的错。** 症状：图在垂直方向拉得极长，循环体跑到最下面。
4. **平行四边形的名称栏宽度是 `w - 20 - 2*(w/6)`**，左右各被斜边吃掉一块。
