# mdj 通用格式

> 所有图类型共用的部分。读某个具体图之前先读这一份。

## 一、文件就是 JSON

`.mdj` 是 UTF-8 JSON，没有二进制部分。用文本编辑器能直接改。

三层结构：

```
Project
└── 模块（FCFlowchart 或 UMLModel）
    ├── Diagram          ← ownedViews 里放所有视图，决定绘制顺序
    └── 元素模型          ← 节点、关系，与视图通过 id 互指
```

**模型层和视图层是两套东西**：模型层说「有哪些元素、谁连谁」，视图层说「画在哪、多大」。两层用同一批 `_id` 串起来。

## 二、id 与引用

- `_id`：24 字符 base64，`base64(os.urandom(16))` 生成。
- **不能含 `/`**（官方样例的字符集里没有它）。
- 引用一律写成 `{"$ref": "<id>"}`。
- 父指针字段名是 **`_parent`**，不是 `parent`。
- `_id` 重复或引用缺失，StarUML 直接打不开。

写完必须自检：收集所有 `_id`，遍历所有 `$ref`，必须全部命中。`scripts/common.py` 的 `selfcheck()` 干这个。

## 三、坐标

- 所有视图的 `left/top/width/height` 是**画布绝对坐标**，不是相对父视图的偏移。
- `LabelView` 的坐标同样是绝对坐标。写相对坐标的典型症状：所有文字挤在左上角。
- 连线视图的 `points` 是 `"x:y;x:y;..."` 字符串，也是绝对坐标。首点落在源视图边界、末点落在目标视图边界，中间的点是拐点。
- `ownedViews` 的顺序决定层级：**后出现的画在上层**。边界框、包这类"背景元素"要放在数组前面。

## 四、两套命名栏，别混

| 场景 | 结构 |
|---|---|
| **Flowchart 扩展**（FCTerminatorView 等） | `subViews` 里直接一个 `LabelView`，视图的 `nameLabel` 指向它 |
| **UML**（UMLClassView / UMLUseCaseView / …） | `subViews` 里一个 `UMLNameCompartmentView`，它内部再包 4 个 `LabelView`（stereotype / name / namespace / property），后三个默认 `visible:false` |

UML 的分类器类视图还要求有 `attributeCompartment` / `operationCompartment` / `receptionCompartment` / `templateParameterCompartment`，缺了会少分隔线或渲染异常。不需要的用 `visible:false` 的空 compartment 占位。

## 五、边的两端

边视图用 `head` / `tail`，**指向视图 id，不是模型 id**。而边的模型用 `source` / `target`，指向模型 id。

```
FCFlow.source  → 模型 id
FCFlowView.tail → 视图 id
```

这两组必须一一对应：`tail` 指向的视图，其 `model` 应当等于 `source`。`mdj.py check` 会查这个。

## 六、多图与默认图

一个工程里可以有多张图，但**只能有一个** Diagram 带 `defaultDiagram: true`。多了 StarUML 行为不确定。

描述文件两种写法：顶层写 `diagram` 出一张图；顶层写 `project` + `views` 出一个工程多张图。
多图时 `mdj.py build` 会自动只保留第一个 `defaultDiagram`，各图名不能重复。

## 七、字体

`font` 统一写 `"Arial;13;0"`，中文能正常显示（系统会 fallback）。

名称栏用 `"Arial;13;1"`（加粗）。

## 八、扩展位：加一种新图

三步：

1. `scripts/` 下新建模块，暴露 `STATUS`（verified / derived）和 `build(spec, project_id) -> dict`，返回一个能直接挂在 Project 下的模块节点。
2. 在 `mdj.py` 的 `MODULES` 字典里登记 `kind -> 模块名`。
3. 写 `references/<类型>.md`，把模型层、视图层的字段结构和踩过的坑记下来。

结构怎么摸（按可靠度排序）：

| 来源 | 可靠度 | 怎么拿 |
|---|---|---|
| 本机同版本 StarUML 生成的同类 mdj | 最高，版本完全匹配 | 找用户以前的作业文件，直接剖结构 |
| `app.asar` 里的 `elements.js` | 高，但只有类定义没有序列化格式 | 见下 |
| 官方样例（jsDelivr） | 中，且经常下不到 | `https://cdn.jsdelivr.net/gh/staruml/staruml-samples@master/<文件>.mdj` |
| 纯推导 | 最低，必须标 derived | 读完类定义推字段 |

抽 `elements.js` 的方法：

```
asar 头部：offset 12 处 uint32 是 header JSON 的字节长度
数据区起点 = 8 + uint32@4
header 里的每个文件的 offset 是**字符串**，要 int() 后再用
```

UML 扩展在 `extensions/essential/uml/elements.js`，流程图在 `extensions/essential/flowchart/elements.js`。

**注意**：`elements.js` 只能告诉你「这个类有哪些属性」，告诉不了你「哪些属性会出现在 JSON 里」。判断依据是构造函数里有没有 `this.xxx = ...`，以及 `update()` 里怎么用。
