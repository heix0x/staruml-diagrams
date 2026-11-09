# staruml-diagrams

Turn a plain description file into a `.mdj` project that StarUML opens directly — no manual
coordinate entry, no hand-written `$ref` chains.

把一份描述文件编译成 StarUML 能直接打开的 `.mdj` 工程。人只写「有哪些元素、谁连谁」，
坐标、id、引用关系由脚本生成。

```bash
python scripts/mdj.py build examples/flowchart-prime.yaml -o out.mdj
python scripts/mdj.py check out.mdj
```

## 安装

解压 zip，把整个 `staruml-diagrams` 目录放进任意一个 skills 目录，**目录名不要改**：

| 放在哪 | 路径 | 效果 |
|---|---|---|
| 全机公共库 | `~/.agents/skills/` | 本机所有 agent 共用 |
| WorkBuddy | `~/.workbuddy/skills/` | 只在 WorkBuddy 里可用 |
| DSH 等其他客户端 | 各自的 `skills/` | 同理 |

```bash
# Windows 示例
Expand-Archive staruml-diagrams-1.0.0.zip -DestinationPath "$env:USERPROFILE\.agents\skills"
```

依赖只有一条，Python 3.10+：

```bash
python -m pip install pyyaml
```

不装 PyYAML 也能用 —— 把描述文件写成 `.json` 即可。

装完确认一遍：

```bash
python scripts/mdj.py build examples/flowchart-prime.yaml -o out.mdj
python scripts/mdj.py check out.mdj
```

两条都通过，说明装好了。

## 你说 → 它做

| 你说 | 它做 |
|---|---|
| 「给我画个素数判断的流程图」 | 写描述文件 → 生成 mdj → 自检 → 提示你打开确认 |
| 「这个 mdj 打不开，看看哪错了」 | `mdj.py check` 定位是引用问题还是结构问题 |
| 「用例图里加个『修改密码』」 | 改描述文件一行，重新 build，其余坐标自动让位 |
| 「类图布局丑」 | 描述文件里加 `at: [x, y]`，或直接改 description 换位置 |

## 覆盖范围

| 图 | 状态 |
|---|---|
| 流程图 flowchart | 已验证（StarUML 5.0.2 打开过） |
| 用例图 usecase | 已验证 |
| 类图 class | 已验证 |
| 构件图 component | 按源码推导，未验证 |
| 部署图 deployment | 按源码推导，未验证 |
| 时序图 sequence | 按源码推导，未验证 |

「未验证」= 字段结构来自 StarUML 源码阅读，逻辑上正确但没实际加载过。第一次用必须开图确认。

## 不适用

- 机器上没 Python、只需要一张流程图 → 用在线版单文件工具，双击网页即用，零安装：
  <https://staruml-flowchart.app.workbuddy.host/?sharecode=3CMKJEEUVJ>
- ER 图 / 状态图 / 活动图 / BPMN / DFD → 尚未实现，扩展方法见 `references/mdj-format.md`
- 想要「自动布局得跟手画一样好看」 → 做不到。类图仍然要手给坐标

## 结构

```
scripts/mdj.py         CLI
scripts/common.py      id、测宽、LabelView、边视图、自检
scripts/dsl.py         描述文件解析
scripts/<图>.py        各图模块，各自暴露 STATUS 和 build()
references/            每种图的结构说明
examples/              可直接 build 的示例
tests/run_checks.py    回归
CHANGELOG.md           版本记录
```

## 原理

`.mdj` 里一半是逻辑（有哪些元素、谁连谁），一半是几何（每个框的坐标、每条线的拐点），
两部分用几十个 `_id` 互相引用。

模型写 JSON 时，逻辑部分写得好，几何部分必崩——因为第 3 个框的 y 取决于前两个框多高，
这是全局约束，逐字生成做不到。

这个工具把两部分拆开：你只提供逻辑，几何由确定性的布局函数算。

## License

MIT
