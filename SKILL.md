---
name: staruml-diagrams
description: 用一份描述文件生成 StarUML 能直接打开的 .mdj 工程文件，覆盖流程图、用例图、类图、构件图、部署图、时序图，自带引用完整性与视图重叠自检。当需要给 StarUML 画图、产出 .mdj、把流程或系统模型转成 StarUML 工程、或者要定位已有 mdj 打不开的原因时使用。
agent_created: true
---

# StarUML 制图

把「要画什么」和「mdj 长什么样」分开。人只写元素和关系，坐标、id、`$ref` 由脚本算。

**为什么需要这个**：`.mdj` 里一半内容是几何信息（每个框的 `left/top/width/height`、每条线的拐点坐标），另一半是几十个互相引用的 `_id`。让模型直接写 JSON，必然出现「框全叠在左上角」或「引用对不上导致文件打不开」。而这个活是确定性的，不该每次重算。

---

## 一、什么时候用

- 要交 StarUML 作业、需要批量出图
- 已有流程图/类图的文字描述，想转成 .mdj
- 别人的 mdj 打不开，需要定位是引用问题还是结构问题
- 要在已有项目里补一张同类图

**不适用 / 先问清楚**：

- 用户只说「帮我画个图」而没说图类型 → 先问是哪种图。不同类型结构完全不同，猜错等于白做。
- 要画的图不在支持列表里（ER / 状态图 / 活动图 / BPMN / DFD）→ 看 `references/mdj-format.md` 末尾的扩展位说明，不要硬套已有模块。
- 目标机没有 Python → 用浏览器版工具（见文末「备选」）。

---

## 二、七条铁律

1. **描述文件里不写坐标。** 坐标由各图模块的布局函数算。唯一例外是类图的 `at: [x, y]`，因为类图自动布局永远不如手调。
2. **生成前 StarUML 必须完全退出。** `mdj.py build` 会检查进程，检测到 StarUML 在跑直接退出（退出码 4）。它在内存里存着打开时的版本、不热重载，你写进去的新文件只要它在界面上保存一次就被盖回去，看起来像「生成了但图没变」。确实要跳过（StarUML 里开的是别的项目）就加 `--force`。
3. **`STATUS: derived` 的图类型，生成后必须让用户在 StarUML 里打开确认。** 不许当成「已完成」交付。确认通过后把 `references/<图>.md` 和脚本里的 `STATUS` 改成 `verified`。
4. **示例只给结构参考，不是模板。** 题目出现示例里没有的元素或关系时，必须先查 `references/<图>.md`，再查本机 `app.asar` 里的 `elements.js` 确认这个元素确实存在，然后才写描述。**禁止因为示例没出现过就省略元素，也禁止硬套示例的结构。**
5. **一个描述文件 = 一张图 = 一个 mdj。** 要多张图就写多个描述文件，不要在同一个文件里塞两张。
6. **`mdj.py check` 不通过就不交付。** 引用不完整、视图重叠这两类问题，StarUML 不会报错，只会显示成一张乱图。
7. **改图改描述文件，不改脚本。** 脚本改动只发生在「布局规则对该类图整体都错了」的时候。

---

## 三、五步流程

### 第 1 步：读题，拆出「元素」和「关系」

把题目里的名词挑成元素，动词挑成关系。验收标准：每个名词都能落到一个 `kind`，每个动词都能落到一个 `relation.kind`。

题目里出现 `kind` 覆盖不了的东西时，停下来做第 4 条铁律要求的两步查证。

### 第 2 步：定图类型

| 题目说 | 用 |
|---|---|
| 步骤、判断、循环、流程 | flowchart |
| 谁用系统、能做什么 | usecase |
| 类、属性、方法、继承 | class |
| 模块、构件、依赖 | component |
| 服务器、节点、部署 | deployment |
| 消息先后顺序、生命线 | sequence |

### 第 3 步：写描述文件

见下一节。放到 `examples/` 旁边，命名 `<图类型>-<主题>.yaml`。

### 第 4 步：生成并自检

```bash
python scripts/mdj.py build 我的图.yaml -o 我的图.mdj
python scripts/mdj.py check  我的图.mdj
```

`build` 打印对象数/引用数和自检结果；`check` 额外查视图重叠、`head/tail` 与 `source/target` 对应、`defaultDiagram` 唯一。

### 第 5 步：让用户打开确认

交付话术固定两句：**先完全退出 StarUML，再双击 mdj**。然后问三件事：能不能打开、元素有没有叠在一起、连线有没有穿过框。

`derived` 图必须走完这一步才算完成。

---

## 四、描述文件语法

单图（一张图一个工程）：

```yaml
diagram:
  kind: flowchart          # 必填，决定用哪个模块
  name: 素数判断流程图        # 必填，显示在 StarUML 的图名
module: 流程图               # 可选，工程树里的模块名，默认取 diagram.name

elements: [...]            # 各图自己解释
relations: [...]           # 可选
```

多图（一个工程多张图，如 4+1 视图）：

```yaml
project: 校园图书借阅系统-4+1视图    # 必填，工程名

views:
  - diagram: {kind: usecase, name: 场景视图-用例图, module: 场景视图}
    elements: [...]
    relations: [...]
  - diagram: {kind: class, name: 逻辑视图-类图, module: 逻辑视图}
    elements: [...]
```

多图的硬约束：**图名不能重复**；`defaultDiagram` 由脚本自动只保留第一个，不要手写。

具体字段按图类型不同，见对应 reference。最小可跑的完整例子在 `examples/`，
六张图合并成工程的完整例子是 `examples/4p1-library.yaml`。

---

## 五、图类型与状态

| kind | 状态 | 依据 | 参考文件 |
|---|---|---|---|
| flowchart | **verified** | 实训4 的两张流程图已在 StarUML 5.0.2 打开 | `references/flowchart.md` |
| usecase | **verified** | 结构抄自本机 test3-修正版.mdj（同版本） | `references/usecase.md` |
| class | **verified** | 结构抄自本机 test1-26-10-11.mdj（同版本） | `references/class.md` |
| component | verified | StarUML 实际加载验证通过 | `references/component.md` |
| deployment | verified | 同上（修复通信路径后验证） | `references/deployment.md` |
| sequence | verified | 同上（两张时序图验证） | `references/sequence.md` |

`derived` 的含义：字段名和嵌套关系来自源码阅读，逻辑上正确，但没有经过 StarUML 实际加载验证。第一次用必须让用户开图确认。

---

## 六、失败怎么退

按顺序，不要跳级：

1. **`build` 报引用自检失败** → 描述文件里 `relations` 引用了不存在的 `elements[].id`。按报错里的名字改描述文件，不要改脚本。
2. **`check` 报视图重叠** → 该类图的布局常量不合适（间距太小），或元素尺寸估算偏小（中文按 13px/字算，超长文本会溢出）。先把图拆成两张，其次调脚本里的 `GAP_*`。
3. **StarUML 打不开** → 先确认是不是没退出 StarUML 就覆盖了文件；再确认 `_id` 无重复、无 `/`。仍不行就看 `mdj.py check` 的报错原文。
4. **打得开但图是乱的** → 坐标问题，不是结构问题。在描述文件里用类图的 `at` 或换布局，不要怀疑字段名。
5. **以上都不行** → 回到 `references/mdj-format.md`，手写一个只有 2 个元素 1 条线的最小 mdj，逐步加元素，定位到具体哪一项有问题。

---

## 七、已知坑

| 现象 | 原因 | 处理 |
|---|---|---|
| 框全叠在左上角 | 视图缺 `left/top`，或用了相对坐标 | 坐标必须是画布绝对坐标 |
| 文件打不开且无提示 | `$ref` 指向不存在的 id | `check` 会列出未命中引用 |
| 连线两端连错元素 | `head/tail` 填了模型 id 而不是视图 id | 边视图的 `head/tail` 是视图 `_id` |
| 改了描述文件但图没变 | StarUML 开着，保存时把旧内容写回 | 完全退出再打开；`build` 现在会拦住运行中的 StarUML |
| 图能打开但一条连线都没有 | 关系只生成了模型，没生成连线视图；或文件被 StarUML 旧版本覆盖 | `check` 报「关系没有连线视图」；退出 StarUML 重生成 |
| 类图属性看不见 | `UMLAttributeCompartmentView` 的 `height` 算小了 | 每个属性 `LINE_H=15`，另加 8px 边距 |
| 菱形/平行四边形文字换行 | 这两类视图的名称栏只有视图宽度的一半 | 视图宽度给足，`wordWrap: false` |

---

## 八、文件清单

```
scripts/mdj.py        CLI：build / check / kinds
scripts/common.py     id 生成、文本测宽、LabelView、边视图、自检
scripts/dsl.py        描述文件解析与校验
scripts/flowchart.py  流程图（verified）
scripts/usecase.py    用例图（verified）
scripts/classdia.py   类图（verified）
scripts/component.py  构件图（verified）
scripts/deployment.py 部署图（verified）
scripts/sequence.py   时序图（verified）
references/           每种图一份结构说明 + 通用格式说明
examples/             最小可跑的描述文件
tests/run_checks.py   对 examples 跑 build + check 的回归
```

## 备选：目标机没有 Python

浏览器版单文件工具（拖进浏览器就能用，不需要任何运行时）适合「陌生电脑 + 只需要一张流程图」的场景。它只做流程图，布局能力比脚本弱，但零安装。

---

## 扩展位

加一种新图类型只需三步：

1. 在 `scripts/` 下新建模块，暴露 `STATUS` 和 `build(spec, project_id) -> dict`
2. 在 `mdj.py` 的 `MODULES` 里登记
3. 写 `references/<类型>.md`，把模型层/视图层结构记下来

结构怎么摸：先找本机同版本 StarUML 生成的同类 mdj 当样板（最可靠），没有就抽 `app.asar` 里 `extensions/essential/uml/elements.js` 看 View 类定义。
