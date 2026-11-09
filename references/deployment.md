# 部署图（kind: deployment）

**状态：derived** — 按 `UMLNodeView` 定义推导，未在 StarUML 打开验证。首次使用必须开图确认。

## 描述文件

```yaml
diagram:
  kind: deployment
  name: 银行储蓄系统-部署图
module: 部署视图

elements:
  - {id: user, kind: actor, text: 用户, at: [80, 100]}
  - {id: app,  kind: node,  text: 系统服务器节点, at: [300, 60], w: 240, h: 330,
     children: [开户, 存款, 取款]}
  - {id: db,   kind: node,  text: 数据服务器节点, at: [740, 140], w: 190, h: 170}

relations:
  - {from: user, to: app}
  - {from: app,  to: db, kind: communication}
```

### 元素

| kind | 画出来 | 字段 |
|---|---|---|
| `node`（默认） | 立方体 | `at`、`w`、`h`、`children`（节点内构件名列表） |
| `component` | 直接放图上的构件 | `at` |
| `actor` | 参与者小人 | `at` |

`children` 里的构件会自动在节点内纵向排开，模型挂在节点模型下、视图挂在节点视图下。

### 关系

| kind | 画出来 |
|---|---|
| `dependency`（默认） | 虚线箭头 |
| `communication` | 实线（节点间通信路径，`UMLCommunicationPath`） |

## 结构

模型层：`UMLModel` → `UMLDeploymentDiagram` + `UMLNode` / `UMLComponent` / `UMLActor` + 关系。

节点内的构件是**两层嵌套**：

```
UMLNode
└── ownedElements: [UMLComponent]     ← 模型挂在节点下
UMLNodeView
└── subViews: [nameCompartment, …, UMLComponentView]   ← 视图挂在节点视图下
```

视图层 `UMLNodeView` 也带五个 compartment，同构件图。

## 坑

1. **节点内构件不能平铺在图上。** 它们必须同时挂两处：模型进节点的 `ownedElements`，视图进节点视图的 `subViews`。只挂一处会显示成游离构件或者干脆不显示。
2. `containerCollapse: false` 要写，否则节点可能以折叠态出现，构件藏在里面。
3. 参与者放在部署图里**不符合 UML 规范**（actor 属于用例图）。但很多教材参考答案这么画，脚本支持。要合规就改用 `node` 表示终端。
4. 节点高度要量够：`children` 每个构件占 90px（60 高 + 30 间距），三个构件至少 h=330。
