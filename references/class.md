# 类图（kind: class）

**状态：verified** — 视图结构抄自本机 `test1-26-10-11.mdj`（7 个类、22 属性、12 关联，同版本打开过）。

## 描述文件

```yaml
diagram:
  kind: class
  name: 银行储蓄系统-类图
module: 逻辑视图

elements:
  - id: 银行账户
    attributes: ["-姓名", "-地址", "-密码"]
    operations: ["+开户()", "+销户()"]
    at: [180, 400]          # 可选，强烈建议给
  - id: 储户
    attributes: ["-姓名", "-地址"]
    at: [180, 620]

relations:
  - {from: 储户, to: 银行账户, kind: association, label: 拥有}
  - {from: 银行系统, to: 存款, kind: association, label: 组成, aggregation: 1}
```

### 元素

| 字段 | 说明 |
|---|---|
| `id` | 元素标识，**同时是显示的类名**（除非另给 `text`） |
| `attributes` | 字符串数组。首字符 `+` 公有、`-` 私有（默认） |
| `operations` | 字符串数组，写法 `+方法名()` |
| `at: [x, y]` | 可选。不给就自动排两列网格，**有 at 的元素先定位，没 at 的排在它们下方** |
| `stereotype` | 可选，显示在类名上方 `«xxx»` |

名称栏用 14px 加粗；属性/操作每行 15px。

### 关系

| kind | 画出来 | 字段 |
|---|---|---|
| `association` | 实线，可带标签 | `label`、`aggregation` |
| `generalization` | 实线空心三角，子类指父类 | 无 |
| `dependency` | 虚线箭头，使用方指被使用方 | `label` |

`aggregation`：`1` = 源端空心菱形（聚合），`2` = 目标端空心菱形，`-1` / `-2` = 实心菱形（组合），`0` 或缺省 = 普通关联。

## 结构

模型层：`UMLModel` → `UMLClassDiagram` + `UMLClass` + `UMLAssociation` / `UMLGeneralization`。

`UMLClass` 里两个特殊字段：

```json
"attributes": [{"_type":"UMLAttribute","name":"姓名","visibility":"private"}],
"operations": [{"_type":"UMLOperation","name":"开户()","visibility":"public"}]
```

`UMLAssociation` 比较特殊：两端是**内嵌对象** `end1` / `end2`（不是 `$ref`），每个 `UMLAssociationEnd` 里用 `reference` 指向类模型。

视图层：`UMLClassView` 必须有五个 compartment 引用：

```
nameCompartment            必须有
attributeCompartment       必须有（空的也要有，高度 8）
operationCompartment       必须有
receptionCompartment       可隐藏
templateParameterCompartment 可隐藏
```

高度算法（和 `classdia.py` 一致）：

```
h = 5 + 25 + (属性数×15 + 8) + (操作数×15 + 8)
名称栏  y+5   高 25
属性栏  y+30  高 属性数×15+8
操作栏  y+30+属性栏高  高 操作数×15+8
```

## 布局规则

类图**不要指望自动布局**。继承树、聚合关系这些，自动排出来的图十次有九次比手画丑。

脚本默认：有 `at` 的按 `at` 放，没有的排两列网格放在下方。实际使用时建议全给 `at`，用坐标把语义摆出来（父类在上、子类在下、被聚合的放右边）。

给坐标时的经验间距：

- 上下相邻的类之间留 60px 以上（类框高度差很大，按最高的那个算）
- 左右相邻留 90px 以上
- 连线密集的一侧（比如"工作人员"连着四个类）把它单独放一行/一列，减少交叉

## 坑

1. **属性看不见**：`attributeCompartment` 的 `height` 小于 `属性数×15+8` 时，最后一行会被裁掉。
2. **类名和 id 的关系**：不写 `text` 时 `id` 就是类名。写中文 id 没问题，但 `relations` 里的 `from/to` 也要写同样的中文。
3. **`UMLAssociationEnd` 是内嵌的**，不是 `$ref`。写成 `{"$ref": ...}` 会导致关联线两端悬空。
4. **聚合菱形方向**：`aggregation: 1` 是源端（`from` 那一端）出现菱形，`2` 是目标端。写反了菱形会跑到错误的一端。
