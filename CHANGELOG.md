# 更新日志

## [1.1.0] - 2026-11-09

### 新增

- 多图工程：描述文件顶层写 `project` + `views`，一个文件出一个工程多张图（如 4+1 视图）
- 类图支持 `kind: dependency`（虚线箭头，使用方指向被使用方）
- `check` 新增「关系没有连线视图」自检：模型在、视图缺，StarUML 里就是一条线都没有
- `build` 检测 StarUML 进程，运行中直接拒绝写入（退出码 4），`--force` 可跳过

### 修复

- 部署图的通信路径整条消失：`UMLCommunicationPath` 是 `UMLAssociation` 的子类，只认 `end1` / `end2`，
  原来按依赖写成 `source` / `target`，StarUML 加载时直接丢弃（模型树里都看不到）
- `check` 新增 `end1/end2` 缺失检测，这条错误以后会被拦住
- `check` 的视图重叠跨图比较，多图工程必误报（一个 6 图工程报了 65 条）
- 用例椭圆、构件、节点下面多出两条空横线：StarUML 每次 `update()` 用 `suppressAttributes` /
  `suppressOperations` 重算 compartment 可见性，只写 `visible: false` 会被覆盖；现在三个开关都写死
- 用例视图补齐 `UMLExtensionPointCompartmentView`（缺了 StarUML 会自己补一个默认的）
- 时序图消息标签没写 `text`，只靠 StarUML 回填，可能整图空白

### 改进

- 用例图支持 `at` 手排坐标；连线改为「能直连就直连，穿框才折线」（原来所有线都挤在同一条通道上，重叠成一片）
- 连线锚点按主方向选：横向间距大走左右、纵向间距大走上下（原来一律走上下，并排节点被连成斜线）
- 时序图生命线间距按最长消息文字自适应（原来固定 700px，三线图散成 1700px 宽）
- 部署图节点高度按 `children` 数量校验

### 状态

- component / deployment / sequence 经 StarUML 实际加载验证，STATUS 由 `derived` 提升为 `verified`
  （实训6 校园图书借阅系统 4+1 视图全程用本 skill 出图并开图确认：构件、部署、时序三类均无异常）

## [1.0.0] - 2026-11-09

首个可用版本。

### 新增

- 六类图生成：flowchart / usecase / class / component / deployment / sequence
- `mdj.py` 三个命令：`build` 生成、`check` 自检、`kinds` 列支持类型
- 描述文件支持 YAML 与 JSON，坐标、`_id`、`$ref` 全部由脚本生成
- 自检项：`$ref` 全命中、无重复 id、`head/tail` 与 `source/target` 一一对应、
  LabelView 文本与模型 name 一致、视图重叠、连线穿框、`defaultDiagram` 唯一
- 六份示例描述文件，`tests/run_checks.py` 一键回归
- `pack.py` 打包脚本

### 已知限制

- component / deployment / sequence 三类结构按 `elements.js` 源码推导，
  未在 StarUML 里实际加载验证（`STATUS: derived`），第一次用需开图确认
- 类图自动布局不如手调，需要精确位置时用 `at: [x, y]`
- 一个描述文件只生成一张图
